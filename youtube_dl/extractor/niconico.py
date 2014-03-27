# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    compat_str,

    ExtractorError,
    unified_strdate,
)


class NiconicoIE(InfoExtractor):
    IE_NAME = 'niconico'
    IE_DESC = 'ニコニコ動画'

    _TEST = {
        'url': 'http://www.nicovideo.jp/watch/sm22312215',
        'md5': 'd1a75c0823e2f629128c43e1212760f9',
        'info_dict': {
            'id': 'sm22312215',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'uploader': 'takuya0301',
            'uploader_id': '2698420',
            'upload_date': '20131123',
            'description': '(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org',
        },
        'params': {
            'username': 'ydl.niconico@gmail.com',
            'password': 'youtube-dl',
        },
    }

    _VALID_URL = r'^https?://(?:www\.|secure\.)?nicovideo\.jp/watch/([a-z][a-z][0-9]+)(?:.*)$'
    _NETRC_MACHINE = 'niconico'

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            # Login is required
            raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)

        # Log in
        login_form_strs = {
            'mail': username,
            'password': password,
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('utf-8')
        request = compat_urllib_request.Request(
            'https://secure.nicovideo.jp/secure/login', login_data)
        login_results = self._download_webpage(
            request, None, note='Logging in', errnote='Unable to log in')
        if re.search(r'(?i)<h1 class="mb8p4">Log in error</h1>', login_results) is not None:
            self._downloader.report_warning('unable to log in: bad username or password')
            return False
        return True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        # Get video webpage. We are not actually interested in it, but need
        # the cookies in order to be able to download the info webpage
        self._download_webpage('http://www.nicovideo.jp/watch/' + video_id, video_id)

        video_info = self._download_xml(
            'http://ext.nicovideo.jp/api/getthumbinfo/' + video_id, video_id,
            note='Downloading video info page')

        # Get flv info
        flv_info_webpage = self._download_webpage(
            'http://flapi.nicovideo.jp/api/getflv?v=' + video_id,
            video_id, 'Downloading flv info')
        video_real_url = compat_urlparse.parse_qs(flv_info_webpage)['url'][0]

        # Start extracting information
        video_title = video_info.find('.//title').text
        video_extension = video_info.find('.//movie_type').text
        video_format = video_extension.upper()
        video_thumbnail = video_info.find('.//thumbnail_url').text
        video_description = video_info.find('.//description').text
        video_uploader_id = video_info.find('.//user_id').text
        video_upload_date = unified_strdate(video_info.find('.//first_retrieve').text.split('+')[0])
        video_view_count = video_info.find('.//view_counter').text
        video_webpage_url = video_info.find('.//watch_url').text

        # uploader
        video_uploader = video_uploader_id
        url = 'http://seiga.nicovideo.jp/api/user/info?id=' + video_uploader_id
        try:
            user_info = self._download_xml(
                url, video_id, note='Downloading user information')
            video_uploader = user_info.find('.//nickname').text
        except ExtractorError as err:
            self._downloader.report_warning('Unable to download user info webpage: %s' % compat_str(err))

        return {
            'id': video_id,
            'url': video_real_url,
            'title': video_title,
            'ext': video_extension,
            'format': video_format,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'uploader': video_uploader,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'view_count': video_view_count,
            'webpage_url': video_webpage_url,
        }

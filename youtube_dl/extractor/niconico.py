# encoding: utf-8

import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    compat_str,

    ExtractorError,
    unified_strdate,
)


class NiconicoIE(InfoExtractor):
    IE_NAME = u'niconico'
    IE_DESC = u'ニコニコ動画'

    _TEST = {
        u'url': u'http://www.nicovideo.jp/watch/sm22312215',
        u'file': u'sm22312215.mp4',
        u'md5': u'd1a75c0823e2f629128c43e1212760f9',
        u'info_dict': {
            u'title': u'Big Buck Bunny',
            u'uploader': u'takuya0301',
            u'uploader_id': u'2698420',
            u'upload_date': u'20131123',
            u'description': u'(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org',
        },
        u'params': {
            u'username': u'ydl.niconico@gmail.com',
            u'password': u'youtube-dl',
        },
    }

    _VALID_URL = r'^https?://(?:www\.|secure\.)?nicovideo\.jp/watch/([a-z][a-z][0-9]+)(?:.*)$'
    _NETRC_MACHINE = 'niconico'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = True

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError(u'No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return False

        # Log in
        login_form_strs = {
            u'mail': username,
            u'password': password,
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('utf-8')
        request = compat_urllib_request.Request(
            u'https://secure.nicovideo.jp/secure/login', login_data)
        login_results = self._download_webpage(
            request, u'', note=u'Logging in', errnote=u'Unable to log in')
        if re.search(r'(?i)<h1 class="mb8p4">Log in error</h1>', login_results) is not None:
            self._downloader.report_warning(u'unable to log in: bad username or password')
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
            note=u'Downloading video info page')

        # Get flv info
        flv_info_webpage = self._download_webpage(
            u'http://flapi.nicovideo.jp/api/getflv?v=' + video_id,
            video_id, u'Downloading flv info')
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
                url, video_id, note=u'Downloading user information')
            video_uploader = user_info.find('.//nickname').text
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'Unable to download user info webpage: %s' % compat_str(err))

        return {
            'id':          video_id,
            'url':         video_real_url,
            'title':       video_title,
            'ext':         video_extension,
            'format':      video_format,
            'thumbnail':   video_thumbnail,
            'description': video_description,
            'uploader':    video_uploader,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'view_count':  video_view_count,
            'webpage_url': video_webpage_url,
        }

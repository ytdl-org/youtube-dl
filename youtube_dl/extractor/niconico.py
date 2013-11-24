# encoding: utf-8

import re
import socket
import xml.etree.ElementTree

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

    _VALID_URL = r'^(?:https?://)?(?:www\.)?nicovideo\.jp/watch/([a-z][a-z][0-9]+)(?:.*)$'
    _LOGIN_URL = 'https://secure.nicovideo.jp/secure/login'
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
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')
        request = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
            if re.search(r'(?i)<h1 class="mb8p4">Log in error</h1>', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username or password')
                return False
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return False
        return True

    def _real_extract(self, url):
        video_id = self._extract_id(url)

        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'http://www.nicovideo.jp/watch/' + video_id
        request = compat_urllib_request.Request(url)
        try:
            video_webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video webpage: %s' % compat_str(err))

        # Get video info
        self.report_video_info_webpage_download(video_id)
        url = 'http://ext.nicovideo.jp/api/getthumbinfo/' + video_id
        request = compat_urllib_request.Request(url)
        try:
            video_info_webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video info webpage: %s' % compat_str(err))

        # Get flv info
        self.report_flv_info_webpage_download(video_id)
        url = 'http://flapi.nicovideo.jp/api/getflv?v=' + video_id
        request = compat_urllib_request.Request(url)
        try:
            flv_info_webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download flv info webpage: %s' % compat_str(err))

        # Start extracting information
        self.report_information_extraction(video_id)
        video_info = xml.etree.ElementTree.fromstring(video_info_webpage)

        # url
        video_real_url = compat_urlparse.parse_qs(flv_info_webpage.decode('utf-8'))['url'][0]

        # title
        video_title = video_info.find('.//title').text

        # ext
        video_extension = video_info.find('.//movie_type').text

        # format
        video_format = video_extension.upper()

        # thumbnail
        video_thumbnail = video_info.find('.//thumbnail_url').text

        # description
        video_description = video_info.find('.//description').text

        # uploader_id
        video_uploader_id = video_info.find('.//user_id').text

        # uploader
        url = 'http://seiga.nicovideo.jp/api/user/info?id=' + video_uploader_id
        request = compat_urllib_request.Request(url)
        try:
            user_info_webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'Unable to download user info webpage: %s' % compat_str(err))

        user_info = xml.etree.ElementTree.fromstring(user_info_webpage)
        video_uploader = user_info.find('.//nickname').text

        # uploder_date
        video_upload_date = unified_strdate(video_info.find('.//first_retrieve').text.split('+')[0])

        # view_count
        video_view_count = video_info.find('.//view_counter').text

        # webpage_url
        video_webpage_url = video_info.find('.//watch_url').text

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

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)
        return video_id

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self.to_screen(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video info webpage' % video_id)

    def report_flv_info_webpage_download(self, video_id):
        """Report attempt to download flv info webpage."""
        self.to_screen(u'%s: Downloading flv info webpage' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self.to_screen(u'%s: Extracting video information' % video_id)

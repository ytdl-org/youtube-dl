#! -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import hashlib

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
)


class FC2IE(InfoExtractor):
    _VALID_URL = r'^http://video\.fc2\.com/((?P<lang>[^/]+)/)?(a/)?content/(?P<id>[^/]+)'
    IE_NAME = 'fc2'
    _NETRC_MACHINE = 'fc2'
    _TEST = {
        'url': 'http://video.fc2.com/en/content/20121103kUan1KHs',
        'md5': 'a6ebe8ebe0396518689d963774a54eb7',
        'info_dict': {
            'id': '20121103kUan1KHs',
            'ext': 'flv',
            'title': 'Boxing again with Puff',
        },
    }

    #def _real_initialize(self):
    #    self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if (username is None) or (password is None):
           self._downloader.report_warning('unable to log in: will be downloading in non authorized mode')
           return False

        # Log in
        login_form_strs = {
            'email':    username,
            'password': password,
            'done':     'video',
            'Submit':   ' Login ',
        }

        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('utf-8')
        request    = compat_urllib_request.Request(
            'https://secure.id.fc2.com/index.php?mode=login&switch_language=en', login_data)

        login_results = self._download_webpage(request, None, note='Logging in', errnote='Unable to log in')
        if 'mode=redirect&login=done' not in login_results:
            self._downloader.report_warning('unable to log in: bad username or password')
            return False
        
        # this is also needed
        login_redir = compat_urllib_request.Request('http://id.fc2.com/?mode=redirect&login=done')
        redir_res   = self._download_webpage(login_redir, None, note='Login redirect', errnote='Something is not right')

        return True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        self._downloader.cookiejar.clear_session_cookies()  # must clear
        self._login()

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        refer = (url if '/a/content/' in url else url.replace('/content/', '/a/content/'));
        mimi = hashlib.md5((video_id + '_gGddgPfeaf_gzyr').encode('utf-8')).hexdigest()

        info_url = (
            "http://video.fc2.com/ginfo.php?mimi={1:s}&href={2:s}&v={0:s}&fversion=WIN%2011%2C6%2C602%2C180&from=2&otag=0&upid={0:s}&tk=null&".
            format(video_id, mimi, compat_urllib_request.quote(refer, safe='').replace('.','%2E')))

        info_webpage = self._download_webpage(
            info_url, video_id, note='Downloading info page')
        info = compat_urlparse.parse_qs(info_webpage)

        if 'err_code' in info:
            #raise ExtractorError('Error code: %s' % info['err_code'][0])
            # most of the time we can still download wideo even if err_code is 403 or 602
            print 'Error code was: %s... but still trying' % info['err_code'][0]
            
        if 'filepath' not in info:
            raise ExtractorError('No file path for download. Maybe not logged?')

        video_url = info['filepath'][0] + '?mid=' + info['mid'][0]
        title_info = info.get('title')
        if title_info:
            title = title_info[0]

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'flv',
            'thumbnail': thumbnail,
        }

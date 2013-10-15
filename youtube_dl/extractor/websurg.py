# coding: utf-8

import re

from ..utils import (
    compat_urllib_request,
    compat_urllib_parse
)

from .common import InfoExtractor

class WeBSurgIE(InfoExtractor):
    IE_NAME = u'websurg.com'
    _VALID_URL = r'http://.*?\.websurg\.com/MEDIA/\?noheader=1&doi=(.*)'

    _TEST = {
        u'url': u'http://www.websurg.com/MEDIA/?noheader=1&doi=vd01en4012',
        u'file': u'vd01en4012.mp4',
        u'params': {
            u'skip_download': True,
        },
        u'skip': u'Requires login information',
    }
    
    _LOGIN_URL = 'http://www.websurg.com/inc/login/login_div.ajax.php?login=1'

    def _real_initialize(self):

        login_form = {
            'username': self._downloader.params['username'],
            'password': self._downloader.params['password'],
            'Submit': 1
        }
        
        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        request.add_header(
            'Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
        compat_urllib_request.urlopen(request).info()
        webpage = self._download_webpage(self._LOGIN_URL, '', 'Logging in')
        
        if webpage != 'OK':
            self._downloader.report_error(
                u'Unable to log in: bad username/password')
        
    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group(1)
        
        webpage = self._download_webpage(url, video_id)
        
        url_info = re.search(r'streamer="(.*?)" src="(.*?)"', webpage)
        
        return {'id': video_id,
                'title': self._og_search_title(webpage),
                'description': self._og_search_description(webpage),
                'ext' : 'mp4',
                'url' : url_info.group(1) + '/' + url_info.group(2),
                'thumbnail': self._og_search_thumbnail(webpage)
                }

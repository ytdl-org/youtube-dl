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
        }
    }
    
    _LOGIN_URL = 'http://www.websurg.com/inc/login/login_div.ajax.php?login=1'

    def _real_extract(self, url):

        login_form = {
            'username': self._downloader.params['username'],
            'password': self._downloader.params['password'],
            'Submit': 1
        }
        
        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        request.add_header(
            'Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
        login_results = compat_urllib_request.urlopen(request).info()
        
        sessid = re.match(r'PHPSESSID=(.*);',
            login_results['Set-Cookie']).group(1)
        request = compat_urllib_request.Request(
            url, compat_urllib_parse.urlencode(login_form),
            {'Cookie': 'PHPSESSID=' + sessid + ';'})
        webpage = compat_urllib_request.urlopen(request).read()
        
        video_id = re.match(self._VALID_URL, url).group(1)
        
        url_info = re.search(r'streamer="(.*?)" src="(.*?)"', webpage)
        
        if url_info is None:
            self._downloader.report_warning(
                u'Unable to log in: bad username/password')
            return
            
        return {'id': video_id,
                'title' : re.search(
                    r'property="og:title" content="(.*?)" />'
                    , webpage).group(1),
                'description': re.search(
                    r'name="description" content="(.*?)" />', webpage).group(1),
                'ext' : 'mp4',
                'url' : url_info.group(1) + '/' + url_info.group(2),
                'thumbnail': re.search(
                    r'property="og:image" content="(.*?)" />', webpage
                ).group(1)
                }

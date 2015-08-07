from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urlparse
)

class XVXIE(InfoExtractor):
    _VALID_URL =r'(?:https?://)?(?:www\.)?xvx\.so/view/(?P<id>\d+)'
    _TEST = {
        'url': 'http://xvx.so/view/205728768',
        'md5': '1befd4eff6bb71b1abbafbfa46333153',
        'info_dict': {
            'id': '205728768',
            'ext': 'flv',
            'title': 'Brazzers - Undersecretary',
            'age_limit': 18
        }
    }


    def _real_extract(self, url):
    	mobj = re.match(self._VALID_URL, url)
    	
    	video_id = mobj.group('id')
    	
        webpage = self._download_webpage(url, video_id)
        
        video_title = self._html_search_regex(r'<title>\s*(.*) watch online for free | xvx.so</title>', webpage, 'title')
        video_url = self._search_regex(r'video_url=(.+?)&', webpage, 'video url')
 		
    	return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'age_limit': 18
        }

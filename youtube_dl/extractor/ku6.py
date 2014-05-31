from __future__ import unicode_literals
import re
from .common import InfoExtractor

class Ku6IE(InfoExtractor):
    _VALID_URL = r'http://v\.ku6\.com/show/(?P<id>[a-zA-Z0-9\-\_]+)(?:\.)*html'
    _TEST = {
        'url': 'http://v.ku6.com/show/JG-8yS14xzBr4bCn1pu0xw...html',
        'info_dict': {
            'id': 'JG-8yS14xzBr4bCn1pu0xw',
            'ext': 'f4v',
            u'title': u'techniques test',
        }
    }



    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        #title = self._html_search_meta('title', webpage, 'title')
        title = self._search_regex(r'<h1 title=.*>(.*?)</h1>', webpage, 'title')
        self.to_screen('title: '+title)

        dataUrl = 'http://v.ku6.com/fetchVideo4Player/'+video_id+'.html'
        jsonData = self._download_json(dataUrl, video_id)
        downloadUrl = jsonData['data']['f']

        return {
            'id': video_id,
            'title': title,
            'url': downloadUrl
            # TODO more properties (see youtube_dl/extractor/common.py)

        }


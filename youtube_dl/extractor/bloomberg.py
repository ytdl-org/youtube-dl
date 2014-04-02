from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BloombergIE(InfoExtractor):
    _VALID_URL = r'https?://www\.bloomberg\.com/video/(?P<name>.+?)\.html'

    _TEST = {
        'url': 'http://www.bloomberg.com/video/shah-s-presentation-on-foreign-exchange-strategies-qurhIVlJSB6hzkVi229d8g.html',
        'md5': '7bf08858ff7c203c870e8a6190e221e5',
        'info_dict': {
            'id': 'qurhIVlJSB6hzkVi229d8g',
            'ext': 'flv',
            'title': 'Shah\'s Presentation on Foreign-Exchange Strategies',
            'description': 'md5:0681e0d30dcdfc6abf34594961d8ea88',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)
        f4m_url = self._search_regex(
            r'<source src="(https?://[^"]+\.f4m.*?)"', webpage,
            'f4m url')
        title = re.sub(': Video$', '', self._og_search_title(webpage))

        return {
            'id': name.split('-')[-1],
            'title': title,
            'url': f4m_url,
            'ext': 'flv',
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }

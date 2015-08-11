# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class AftenpostenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?aftenposten\.no/webtv/(?:#!/)?video/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.aftenposten.no/webtv/#!/video/21039/trailer-sweatshop-i-can-t-take-any-more',
        'md5': 'fd828cd29774a729bf4d4425fe192972',
        'info_dict': {
            'id': '21039',
            'ext': 'mov',
            'title': 'TRAILER: "Sweatshop" - I can´t take any more',
            'description': 'md5:21891f2b0dd7ec2f78d84a50e54f8238',
            'timestamp': 1416927969,
            'upload_date': '20141125',
        }
    }

    def _real_extract(self, url):
        return self.url_result('xstream:ap:%s' % self._match_id(url), 'Xstream')

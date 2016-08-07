# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SonyLIVIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?sonyliv\.com/details/episodes/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.sonyliv.com/details/episodes/5024612095001/Ep.-1---Achaari-Cheese-Toast---Bachelor\'s-Delight',
        'info_dict': {
            'title': 'Ep. 1 - Achaari Cheese Toast - Bachelor\'s Delight',
            'id': '5024612095001',
            'ext': 'mp4',
            'upload_date': '20160707',
            'description': 'Bachelor\'s Delight is a new food show from Sony LIV to satisfy the taste buds of all those bachelors looking for a quick bite.',
            'uploader_id': '4338955589001',
            'timestamp': 1467870968,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['BrightcoveNew'],
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/4338955589001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        return self.url_result(self.BRIGHTCOVE_URL_TEMPLATE % self._match_id(url), 'BrightcoveNew')

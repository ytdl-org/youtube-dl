# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    unified_timestamp,
)

import re

class FranceInterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceinter\.fr/emissions/(?P<id>[^?#]+)'

    _TEST = {
        'url': 'https://www.franceinter.fr/emissions/la-tete-au-carre/la-tete-au-carre-30-juin-2016',
        'md5': 'f13e4371662cf5a829f64d829ae78062',
        'info_dict': {
            'id': 'la-tete-au-carre/la-tete-au-carre-30-juin-2016',
            'ext': 'mp3',
            'title': 'Regards sur le sport du 30 juin 2016 - France Inter',
            'description': 'UEFA Europa, Jeux Olympiques... La période est aux sports, dans les gradins ou devant les écrans. Mais quel est le regard des spécialistes sur cette pratique? ',
            'timestamp': 1467244800,
            'upload_date': '20160630',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'<button class="replay-button playable" data-is-aod="1" data-url="([^"]+)"', webpage, 'video url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        
        extractdate = self._search_regex(
            r'([0-9]+[.][0-9]+[.][0-9]+)', video_url, 'extractdate', fatal=False)
        
        timestamp = unified_timestamp(extractdate)
            
        upload_date = (unified_strdate(extractdate))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'formats': [{
                'url': video_url,
                'vcodec': 'none',
            }],
        }
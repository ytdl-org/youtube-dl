# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LA7IE(InfoExtractor):
    IE_NAME = 'la7.tv'
    _VALID_URL = r'https?://(?:www\.)?la7\.it/([^/]+)/(?:rivedila7|video)/(?P<id>.+)'

    _TEST = {
        'url': 'http://www.la7.it/crozza/video/inccool8-02-10-2015-163722',
        'md5': '8b613ffc0c4bf9b9e377169fc19c214c',
        'info_dict': {
            'id': '0_42j6wd36',
            'ext': 'mp4',
            'title': 'Inc.Cool8',
            'thumbnail': 're:http://.*\.jpg',
            'description': 'Benvenuti nell\'incredibile mondo della INC. COOL. 8. dove “INC.” sta per “Incorporated” “COOL” sta per “fashion” ed Eight sta per il gesto  atletico',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(r'"entry_id"(?:\s*):(?:\s*)"([^"]+)"', webpage, 'video ID')
        video_url = self._search_regex(r'src_mp4(?:\s*):(?:\s*)"([^"]+)"', webpage, 'video URL')

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }

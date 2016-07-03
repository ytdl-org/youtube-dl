# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    unified_timestamp,
    month_by_french_name,
)

import re

class FranceInterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceinter\.fr/emissions/(?P<id>[^?#]+)'

    _TEST = {
        'url': 'https://www.franceinter.fr/emissions/la-marche-de-l-histoire/la-marche-de-l-histoire-18-decembre-2013',
        'md5': '4764932e466e6f6c79c317d2e74f6884',
        'info_dict': {
            'id': 'la-marche-de-l-histoire/la-marche-de-l-histoire-18-decembre-2013',
            'ext': 'mp3',
            'title': 'L’Histoire dans les jeux vidéo du 18 décembre 2013 - France Inter',
            'description': 'L’Histoire dans les jeux vidéo du 18 décembre 2013  par Jean Lebrun en replay sur France Inter. Retrouvez l\'émission en réécoute gratuite et abonnez-vous au podcast !',
            'timestamp': 1387324800,
            'upload_date': '20131218',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'<button class="replay-button playable" data-is-aod="1" data-url="([^"]+)"', webpage, 'video url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        
        extractdate = self._html_search_regex(
            r'<span class="header-main-content-date">(.*?)</span>', webpage, 'extractdate', fatal=False)
            
        extractdate = extractdate.split()
        
        extractdate = extractdate[3]+","+str(month_by_french_name(extractdate[2]))+","+extractdate[1]
        
        upload_date = unified_strdate(extractdate)
        
        timestamp = unified_timestamp(extractdate)

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
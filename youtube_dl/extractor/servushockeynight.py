# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class servushockeynightIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?servushockeynight\.com/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://servushockeynight.com/videos/runde-17-graz-vs-kac-das-ganze-spiel-zum-nachsehen/',
        'md5': '7ff5e10e45e08062fb94270b88a39948',
        'info_dict': {
            'id': '5857499729001',
            'ext': 'mp4',
            'title': 'Runde 17: Graz vs. Klagenfurt // Saison 18/19 - Ganzes Spiel',
	    'timestamp': 1541359757,
	    'uploader_id': '3213846503001',
	    'upload_date': '20181104',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
        }

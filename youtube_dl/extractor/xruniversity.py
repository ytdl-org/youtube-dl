# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class XruniversityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xruniversity\.com/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.xruniversity.com/bdsm-lets-begin-melissa-moore/',
        'md5': 'cddc9fb8a8644a0a7742149eee95080b',
        'info_dict': {
            'id': 'bdsm-lets-begin-melissa-moore',
            'ext': 'mp4',
            'title': 'BDSM Let’s Begin with Melissa Moore',
            'age_limit': 18,
            'language': 'en-US',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1 class="entry-title">(.+?)</h1>', webpage, 'title')
        hoster_video_id = self._html_search_regex(r'<iframe id="vzvd-(.+?)" class="video-player"', webpage, 'hoster_video_id')
        video_url = "http://view.vzaar.com/"+hoster_video_id+"/video?origin=iframe"
        thumbnail_url = self._html_search_regex(r'<h1 class="entry-title">(.+?)</h1>', webpage, 'thumbnail_url')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'age_limit': 18,
            'ext': 'mp4',
            'language': 'en-US',
        }

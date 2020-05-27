# coding: utf-8
from __future__ import unicode_literals

from .viddler import ViddlerBaseIE


class BritishCouncilIE(ViddlerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?:learnenglish\.)?britishcouncil.org/(?P<id>.*)'
    _TEST = {
        'url': 'https://learnenglish.britishcouncil.org/episode-01-they-meet',
        'md5': '796e9c4fa07017e3da79d5e99ef36fe8',
        'info_dict': {
            'id': '34d5e84c',
            'ext': 'mp4',
            'title': 'StartingOut.s01e01',
            'upload_date': '20160927',
            'uploader': 'BCLearnenglish',
            'timestamp': 1474975664,
            'view_count': int,
            'comment_count': int,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._html_search_regex(
            r'data-video-id=([\'"])(?P<id>[^\'"]+)\1',
            webpage, 'video ID', group='id', default=None)
        return self._extract_viddler_info(url, video_id, None)

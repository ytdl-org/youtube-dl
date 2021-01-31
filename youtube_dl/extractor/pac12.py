# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class Pac12IE(InfoExtractor):
    _VALID_URL = r'https?://(?:[a-z]+\.)?pac-12.com/(?:embed/)?(?P<id>.*)'

    _TEST = {
        'url': 'https://pac-12.com/videos/2020-pac-12-womens-basketball-media-day-arizona-cal-stanford',
        'md5': 'b2e3c0cb99458c8b8e2dc22cb5ac922d',
        'info_dict': {
            'id': 'vod-VGQNKGlo9Go',
            'ext': 'mp4',
            'title': '2020 Pac-12 Women\'s Basketball Media Day - Arizona, Cal & Stanford | Pac-12',
            'description': 'During the 2020 Pac-12 Women\'s Basketball Media Day, Ros Gold-Onwude moderates a discussion with Arizona\'s Adia Barnes & Aari McDonald, Cal\'s Charmin Smith & Evelien Lutje Schipholt & Stanford\'s Tara VanDerveer & Kiana Williams.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = \
            self._search_regex(r'"manifest_url":"(?P<url>https:[^"]+)"',
                               webpage, 'url', group='url', default=None)
        vod_url = None
        if (video_url is None) or ('vod-' not in url):
            vod_url = self._search_regex(r'(https?://(?:embed\.)?pac-12\.com/(?:embed/)?vod-[0-9a-zA-Z]+)',
                                         webpage, 'url', default=None)
        if video_url is None:
            if vod_url is None:
                return None
            return self.url_result(vod_url)
        video_url = re.sub(r'\\', '', video_url)
        title = self._html_search_regex(r'<title>(.+?)</title>', 
                                        webpage, 'title')
        if 'vod-' not in url and vod_url is not None:
            video_id = self._match_id(vod_url)
        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': video_url,
            'ext': 'mp4',
        }

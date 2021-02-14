# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class Pac12IE(InfoExtractor):
    _VALID_URL = r'https?://(?:[a-z]+\.)?pac-12.com/(?:embed/)?(?P<id>.*)'

    _TESTS = [{
        'url': 'https://pac-12.com/videos/2020-pac-12-womens-basketball-media-day-arizona-cal-stanford',
        'md5': 'b2e3c0cb99458c8b8e2dc22cb5ac922d',
        'info_dict': {
            'id': 'vod-VGQNKGlo9Go',
            'ext': 'mp4',
            'title': '2020 Pac-12 Women\'s Basketball Media Day - Arizona, Cal & Stanford',
            'description': 'During the 2020 Pac-12 Women\'s Basketball Media Day, Ros Gold-Onwude moderates a discussion with Arizona\'s Adia Barnes & Aari McDonald, Cal\'s Charmin Smith & Evelien Lutje Schipholt & Stanford\'s Tara VanDerveer & Kiana Williams. ',
        }
    }, {
        'url': 'https://pac-12.com/article/2020/11/24/sonoran-dog-dish-presented-tums',
        'md5': 'a7a8ac72273b9468924bc058cc220d37',
        'info_dict': {
            'id': 'vod-YLMKpNLZvR0',
            'ext': 'mp4',
            'title': 'Sonoran Dog | The Dish, presented by TUMS',
            'description': 'Pac-12 Networks introduces "The Dish," presented by Tums. Jaymee Sire is bringing fans a closeup to game day treats from around the Conference with each treat connecting to a Pac-12 school, bringing the flavor and recipes fans know and love right to the dish! As Arizona and USC basketball seasons tip off, the first feature item from "The Dish" is the Sonoran Dog, a beloved treat by Trojans & Wildcat fans.',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        drupal_settings = self._parse_json(
            self._search_regex(
                r'<script[^>]+type="application/json"[^>]*data-drupal-selector="drupal-settings-json">([^<]+)</script>',
                webpage, 'drupal settings'), video_id)

        cv = drupal_settings.get('currentVideo', {})
        manifest_url = cv.get('manifest_url')

        if manifest_url is None:
            # Video may be embedded one level deeper
            vod_url = self._search_regex(
               r'(https?://(?:embed\.)?pac-12\.com/(?:embed/)?vod-\w+)',
                webpage, 'url', default=None)
            if vod_url is None:
                return None
            return self.url_result(vod_url)

        return {
            'id': cv.get('id'),
            'title': cv.get('title'),
            'description': cv.get('description'),
            'url': manifest_url,
            'ext': 'mp4',
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import try_get


class Pac12IE(InfoExtractor):
    _VALID_URL = r'https?://(?:[a-z]+\.)?pac-12.com/(?:embed/)?(?P<id>.*)'

    _TESTS = [{
        'url': 'https://pac-12.com/videos/2020-pac-12-womens-basketball-media-day-arizona-cal-stanford',
        'md5': 'c134cb64fc884658497690dca50094a3',
        'info_dict': {
            'id': 'vod-VGQNKGlo9Go',
            'ext': 'mp4',
            'title': '2020 Pac-12 Women\'s Basketball Media Day - Arizona, Cal & Stanford',
            'description': 'During the 2020 Pac-12 Women\'s Basketball Media Day, Ros Gold-Onwude moderates a discussion with Arizona\'s Adia Barnes & Aari McDonald, Cal\'s Charmin Smith & Evelien Lutje Schipholt & Stanford\'s Tara VanDerveer & Kiana Williams. ',
        }
    }, {
        'url': 'https://pac-12.com/article/2020/11/24/sonoran-dog-dish-presented-tums',
        'md5': 'a91ae1eaf05cea2c5dbe6c1ab7997cc3',
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

        cv = drupal_settings.get('currentVideo')

        if cv is False:
            # May be an event page; look for the live stream.
            network = try_get(drupal_settings,
                              lambda x: x['pac12_react'][
                                  'pac12_react_event_widget']['event'][
                                  'broadcast_info']['broadcast_networks'][0][
                                  'id'], int)
            if network is not None:
                cv = try_get(drupal_settings,
                             lambda x: x['pac12_react']['networks'][
                                 str(network)], dict)

        if not cv or 'manifest_url' not in cv:
            # Video may be embedded one level deeper; look for embed URL.
            vod_url = self._search_regex(
                r'(https?://(?:embed\.)?pac-12\.com/(?:embed/)?vod-\w+)',
                webpage, 'url', default=None)
            if vod_url is None:
                # Failure; no video found.
                return None
            return self.url_result(vod_url)

        return {
            # cv['id'] might be an integer, string, or missing.
            'id': compat_str(cv.get('id') or video_id),
            'title': (cv.get('title')
                      or self._html_search_meta(
                          ['og:title', 'twitter:title',
                           'branch.deeplink.title'], webpage)
                      or self._html_search_regex(r'<title>(.+?)</title>',
                                                 webpage, 'title')),
            'description': (cv.get('description')
                            or self._html_search_meta(
                                ['og:description', 'twitter:description',
                                 'description'], webpage, fatal=False)),
            'url': cv['manifest_url'],
            'ext': 'mp4',
        }

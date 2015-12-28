from __future__ import unicode_literals

from .common import InfoExtractor


class GoldenMoustacheIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?goldenmoustache\.com/(?P<display_id>[\w-]+)-(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.goldenmoustache.com/suricate-le-poker-3700/',
        'md5': '0f904432fa07da5054d6c8beb5efb51a',
        'info_dict': {
            'id': '3700',
            'ext': 'mp4',
            'title': 'Suricate - Le Poker',
            'description': 'md5:3d1f242f44f8c8cb0a106f1fd08e5dc9',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.goldenmoustache.com/le-lab-tout-effacer-mc-fly-et-carlito-55249/',
        'md5': '27f0c50fb4dd5f01dc9082fc67cd5700',
        'info_dict': {
            'id': '55249',
            'ext': 'mp4',
            'title': 'Le LAB - Tout Effacer (Mc Fly et Carlito)',
            'description': 'md5:9b7fbf11023fb2250bd4b185e3de3b2a',
            'thumbnail': 're:^https?://.*\.(?:png|jpg)$',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'data-src-type="mp4" data-src="([^"]+)"', webpage, 'video URL')
        title = self._html_search_regex(
            r'<title>(.*?)(?: - Golden Moustache)?</title>', webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }

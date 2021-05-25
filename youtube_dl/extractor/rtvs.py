# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RTVSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtvs\.sk/(?:radio|televizia)/archiv/\d+/(?P<id>\d+)'
    _TESTS = [{
        # radio archive
        'url': 'https://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '414872',
            'ext': 'mp3',
            'title': 'Ostrov pokladov 1 časť.mp3'
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # tv archive
        'url': 'https://www.rtvs.sk/televizia/archiv/8249/63118',
        'md5': '85e2c55cf988403b70cac24f5c086dc6',
        'info_dict': {
            'id': '63118',
            'ext': 'mp4',
            'title': 'Amaro Džives - Náš deň',
            'description': 'Galavečer pri príležitosti Medzinárodného dňa Rómov.'
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        json_url = self._search_regex(
            r'url\s*=\s*[\'"](?P<url>//www.rtvs.sk/json/[^&"\']+)', webpage,
            'json url', group='url')

        data = self._download_json('https:' + json_url, video_id)

        if json_url.find('audio') >= 0:

            playlist0 = data.get("playlist")[0]
            title = playlist0.get("title")
            url = playlist0.get('sources')[0].get('src')
            return {'id': video_id, 'title': title, 'url': url}

        else:

            clip = data.get("clip")
            description = clip.get("description")
            title = clip.get("title")
            url = clip.get("sources")[0].get('src')
            return {'id': video_id, 'ext': 'mp4', 'title': title, 'description': description, 'url': url}

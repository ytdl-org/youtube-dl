# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NarandoPlayerIE(InfoExtractor):
    IE_NAME = "narando:player"
    _VALID_URL = r'https://narando.com/widget\?r=(?P<id>\w+)'
    _TEST = {
        'url': 'https://narando.com/widget?r=b2t4t789kxgy9g7ms4rwjvvw',
        'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
        'info_dict': {
            'id': 'b2t4t789kxgy9g7ms4rwjvvw',
            'ext': 'mp3',
            'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            'url': 'https://static.narando.com/sounds/10492/original.mp3',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://narando.com/widget?r=' + video_id, video_id)
        title = self._html_search_regex(r'<title>narando \| (.+?)</title>', webpage, 'title')
        download_url = self._html_search_regex(r'.<div class="stream_url hide">\s*([^?]*)', webpage, 'download_url')

        return {
            'id': video_id,
            'title': title,
            'url': download_url,
        }


class NarandoIE(InfoExtractor):
    IE_NAME = "narando"
    _VALID_URL = r'https?://(?:www\.)?narando\.com/articles/(?P<id>([a-zA-Z]|-)+)'
    _TEST = {
        'url': 'https://narando.com/articles/an-ihrem-selbstlob-erkennt-man-sie',
        'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
        'info_dict': {
            'id': 'b2t4t789kxgy9g7ms4rwjvvw',
            'ext': 'mp3',
            'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            'url': 'https://static.narando.com/sounds/10492/original.mp3',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://narando.com/articles/' + video_id, video_id)
        title = self._html_search_regex(r'<h1 class="visible-xs h3">(.+?)</h1>', webpage, 'title')
        player_id = self._html_search_regex(r'[\n\r].*https:\/\/narando.com\/r\/\s*([^"]*)', webpage, 'player_id')
        player_url = 'https://narando.com/widget?r=' + player_id

        return {
            'id': player_id,
            'title': title,
            'url': player_url,
            '_type': 'url',
        }

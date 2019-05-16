# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NarandoIE(InfoExtractor):
    IE_NAME = 'narando'
    _THUMB_SIZES = ('small', 'square', 'medium', 'big', 'original')
    _VALID_URL = r'https?://narando\.com/widget\?.*?r=(?P<id>\w+)&?'
    _TEST = {
        'url': 'https://narando.com/widget?r=b2t4t789kxgy9g7ms4rwjvvw',
        'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
        'info_dict': {
            'id': 'b2t4t789kxgy9g7ms4rwjvvw',
            'ext': 'mp3',
            'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<span class="clip-title">(.+?)</span>', webpage, 'title')
        download_url = self._html_search_regex(r'<div class="stream_url hide">(.+)</div>', webpage, 'download_url')
        thumbnail_id = self._html_search_regex(r'article_picture\/(.+?)\/small\.jpg', webpage, 'thumbnail_id', fatal=False)
        thumbnail_dict = []
        thumb_id = 0
        for size in self._THUMB_SIZES:
            thumbnail_dict.append({
                'url': 'https://static.narando.com/article_picture/' + thumbnail_id + '/' + size + '.jpg',
                'id': size,
                'preference': thumb_id,
            })
            thumb_id += 1
        return {
            'id': video_id,
            'title': title,
            'url': download_url,
            'vcodec': 'none',
            'thumbnails': thumbnail_dict,
        }


class NarandoArticleIE(InfoExtractor):
    IE_NAME = "narando:article"
    _VALID_URL = r'https?://(?:www\.)?narando\.com/(articles|r)/(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://narando.com/articles/an-ihrem-selbstlob-erkennt-man-sie',
            'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
            'info_dict': {
                'id': 'b2t4t789kxgy9g7ms4rwjvvw',
                'ext': 'mp3',
                'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            }
        },
        {
            'url': 'https://narando.com/r/b2t4t789kxgy9g7ms4rwjvvw',  # alternate URL format
            'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
            'info_dict': {
                'id': 'b2t4t789kxgy9g7ms4rwjvvw',
                'ext': 'mp3',
                'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1 class="visible-xs h3">(.+?)</h1>', webpage, 'title')
        player_id = self._html_search_regex(r'https://narando.com/r/(.+?)\"', webpage, 'player_id')
        url_result = 'https://narando.com/widget?r=' + player_id

        return {
            'id': player_id,
            'title': title,
            'url': url_result,
            '_type': 'url',
        }

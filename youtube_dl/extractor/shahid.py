# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    ExtractorError,
    int_or_none
)


class ShahidIE(InfoExtractor):
    _VALID_URL = r'https?://shahid\.mbc\.net/ar/episode/(?P<id>\d+)/?'
    _TESTS = [
        {
            'url': 'https://shahid.mbc.net/ar/episode/108084/%D8%AE%D9%88%D8%A7%D8%B7%D8%B1-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-11-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1.html',
            'info_dict': {
                'id': '108084',
                'ext': 'm3u8',
                'title': 'خواطر الموسم 11 الحلقة 1',
                'description': 'بسم الله',
                'duration': 1166,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            }
        },
        {
            # shahid plus subscriber only
            'url': 'https://shahid.mbc.net/ar/series/90497/%D9%85%D8%B1%D8%A7%D9%8A%D8%A7-2011.html',
            'only_matching': True
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_info = ''
        for line in self._search_regex('var flashvars = ({[^}]+})', webpage, 'flashvars').splitlines():
            if '+' not in line and '(' not in line and ')' not in line:
                player_info += line
        player_info = self._parse_json(js_to_json(player_info), video_id)
        video_id = player_info['id']
        player_type = player_info['playerType']

        player_json_data = self._download_json(
            'https://shahid.mbc.net/arContent/getPlayerContent-param-.id-' + video_id + '.type-' + player_info['type'] + '.html',
            video_id
        )['data']
        if 'url' in player_json_data:
            m3u8_url = player_json_data['url']
        else:
            for error in player_json_data['error'].values():
                raise ExtractorError(error)
        formats = self._extract_m3u8_formats(m3u8_url, video_id)

        video_info = self._download_json(
            player_info['url'] + '/' + player_type + '/' + video_id + '?apiKey=sh%40hid0nlin3&hash=b2wMCTHpSmyxGqQjJFOycRmLSex%2BBpTK%2Fooxy6vHaqs%3D',
            video_id
        )['data']
        if video_info.get('error'):
            for error in video_info['error']:
                raise ExtractorError(error)
        video_info = video_info[player_type]
        title = video_info['title']
        thumbnail = video_info.get('thumbnailUrl')
        categories = [category['name'] for category in video_info.get('genres')]
        description = video_info.get('description')
        duration = int_or_none(video_info.get('duration'))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'categories': categories,
            'description': description,
            'duration': duration,
            'formats': formats,
        }

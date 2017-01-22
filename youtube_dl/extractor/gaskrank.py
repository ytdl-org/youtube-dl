# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import js_to_json


class GaskrankIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gaskrank\.tv/tv/(?P<categories>[^/]+)/(?P<id>[^/]+)\.html?'
    _TEST = {
        'url': 'http://www.gaskrank.tv/tv/motorrad-fun/strike-einparken-durch-anfaenger-crash-mit-groesserem-flurschaden.htm',
        'md5': '1ae88dbac97887d85ebd1157a95fc4f9',
        'info_dict': {
            'id': '201601/26955',
            'ext': 'mp4',
            'title': 'Strike! Einparken können nur Männer - Flurschaden hält sich in Grenzen *lol*',
            'thumbnail': r're:^https?://.*\.jpg$',
            'categories': ['motorrad-fun'],
            'display_id': 'strike-einparken-durch-anfaenger-crash-mit-groesserem-flurschaden',
        }
    }

    def _real_extract(self, url):
        def fix_json(code):
            return re.sub(r'}[\s]*?,[\s]*?}', r'}}', js_to_json(code))

        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        categories = [re.match(self._VALID_URL, url).group('categories')]
        title = self._search_regex(r'movieName\s*:\s*\'([^\']*)\'', webpage, 'title')
        thumbnail = self._search_regex(r'poster\s*:\s*\'([^\']*)\'', webpage, 'thumbnail', default=None)
        playlist = self._parse_json(
            self._search_regex(r'playlist\s*:\s*\[([^\]]*)\]', webpage, 'playlist', default='{}'),
            display_id, transform_source=fix_json, fatal=False)
        video_id = self._search_regex(r'https?://movies\.gaskrank\.tv/([^-]*?)(-[^\.]*)?\.mp4', playlist.get('0').get('src'), 'video id')
        formats = []
        for key in playlist:
            formats.append({
                'url': playlist[key]['src'],
                'format_id': key,
                'quality': playlist[key].get('quality')})
        self._sort_formats(formats, field_preference=['format_id'])

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'categories': categories,
            'display_id': display_id,
        }

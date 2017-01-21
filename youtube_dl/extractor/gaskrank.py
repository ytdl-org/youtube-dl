# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import js_to_json


class GaskrankIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gaskrank\.tv/tv(?:/[^/]+)+/(?P<id>[^/]+)\.htm'
    _TEST = {
        'url': 'http://www.gaskrank.tv/tv/motorrad-fun/strike-einparken-durch-anfaenger-crash-mit-groesserem-flurschaden.htm',
        'md5': '200e28a405f6919b914a83f8adfc5739',
        'info_dict': {
            'id': '201601/26955',
            'ext': 'mp4',
            'title': 'Strike! Einparken können nur Männer - Flurschaden hält sich in Grenzen *lol*',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        def fix_json(code):
            return re.sub(r'}[\s]*?,[\s]*?}', r'}}', js_to_json(code))

        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(r'https?://movies\.gaskrank\.tv/([^-]*?)\.mp4', webpage, 'video id')
        categories = self._search_regex(r'https?://(?:www\.)?gaskrank\.tv/tv(?:/([^/]+))+/[^/]+\.htm', url, 'categories', default=None)
        title = self._search_regex(r'movieName[^\']*?\'([^\']*?)\'', webpage, 'title')
        thumbnail = self._search_regex(r'poster[^\']*?\'([^\']*?)\'', webpage, 'thumbnail', default=None)
        playlist = self._parse_json(
            self._search_regex(r'playlist:[\s\S]*?\[([\s\S]*?)]', webpage, 'playlist', default='{}'),
            video_id, transform_source=fix_json, fatal=False)
        formats = []
        for key in sorted(playlist):
            formats.append({
                'url': playlist[key]['src'],
                'format_id': key,
                'quality': playlist[key].get('quality'),
                'resolution': playlist[key].get('quality')})

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'categories': categories,
            'display_id': display_id,
        }

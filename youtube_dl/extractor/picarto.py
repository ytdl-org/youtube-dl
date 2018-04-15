# coding: utf-8
import re

from __future__ import unicode_literals

from .common import InfoExtractor

class PicartoVodIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?picarto\.tv/videopopout/(?P<id>[a-zA-Z_\-.0-9]+).flv'
    _TEST = {
        'url': 'https://picarto.tv/videopopout/Carrot_2018.01.11.07.55.12.flv',
        'md5': '1ecd32f358fee23d8b3e6954880f78d4',
        'info_dict': {
            'id': 'Carrot_2018.01.11.07.55.12',
            'ext': 'm3u8',
            'title': 'Carrot_2018.01.11.07.55.12',
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vod_regex = r'<script[^<]*>[^<]*riot\.mount\([^<]+({[^<]+})\)[^<]*<\/script>'
        script = self._html_search_regex(vod_regex, webpage, 'vod_script')
        
        print("penis", script)
        
        params = self._parse_json(script, video_id, lambda x : re.sub(r'(\w+)(:\s+)', '"$1"$2', x));
        
        title = video_id
        url = params.vod
        thumb = params.vodThumb
        
        return {
            'id': video_id,
            'title': title,
            'url' : url,
            'thumbnail' : thumb
        }

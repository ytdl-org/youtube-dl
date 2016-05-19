# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor

from ..utils import (
    unescapeHTML,
    int_or_none,
)

class MSNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?msn\.com/[a-z-]{2,5}(?:/[a-z]+)+/(?P<display_id>[a-z-]+)/[a-z]{2}-(?P<id>[a-zA-Z]+)'
    _TESTS = [{
        'url': 'http://www.msn.com/en-ae/foodanddrink/joinourtable/criminal-minds-shemar-moore-shares-a-touching-goodbye-message/vp-BBqQYNE',
        'info_dict': {
            'id': 'BBqQYNE',
            'title': 'Criminal Minds - Shemar Moore Shares A Touching Goodbye Message',
            'description': 'md5:e8e89b897b222eb33a6b5067a8f1bc25',
            'duration': 104,
            'ext': 'mp4',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.msn.com/en-ae/news/offbeat/meet-the-nine-year-old-self-made-millionaire/ar-BBt6ZKf',
        'info_dict': {
            'id': 'BBt6ZKf',
            'title': 'All That Bling: Self-Made Millionaire Child Builds Fashion & Jewellery Empire',
            'description': 'md5:8e683bd5c729d5fb16d96539a582aa5e',
            'duration': 350,
            'ext': 'mp4',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        self.report_extraction(display_id)
        video_data = self._parse_json(self._html_search_regex(r'data-metadata\s*=\s*["\'](.+)["\']',
            webpage, 'video data'), display_id)

        formats = []
        for video_file in video_data.get('videoFiles', []):
            if not '.ism' in video_file.get('url', '.ism'):
                formats.append({
                    'url': unescapeHTML(video_file.get('url')),
                    'ext': 'mp4',
                    'width': int_or_none(video_file.get('width')),
                    'height': int_or_none(video_file.get('height')),
                })
            elif 'm3u8' in video_file.get('url'):
                formats.extend(self._extract_m3u8_formats(
                    video_file.get('url'), display_id, 'mp4'))
            # There (often) exists an Microsoft Smooth Streaming manifest
            # (.ism) which is not yet supported
            # (https://github.com/rg3/youtube-dl/issues/8118)

        self._sort_formats(formats)

        subtitles = {}
        for f in video_data.get('files', []):
            if f.get('formatCode', '') == '3100':
                lang = f.get('culture', '')
                if not lang:
                    continue
                subtitles.setdefault(lang, []).append({
                    'ext': 'ttml',
                    'url': unescapeHTML(f.get('url')),
                })

        return {
            'id': video_id,
            'title': video_data['title'],
            'formats': formats,
            'thumbnail': video_data.get('headlineImage', {}).get('url'),
            'description': video_data.get('description'),
            'creator': video_data.get('creator'),
            'subtitles': subtitles,
            'duration': int_or_none(video_data.get('durationSecs')),
        }

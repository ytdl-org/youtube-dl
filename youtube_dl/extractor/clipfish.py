from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
    parse_iso8601,
    remove_end,
)


class ClipfishIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?clipfish\.de/(?:[^/]+/)+video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.clipfish.de/special/game-trailer/video/3966754/fifa-14-e3-2013-trailer/',
        'md5': '79bc922f3e8a9097b3d68a93780fd475',
        'info_dict': {
            'id': '3966754',
            'ext': 'mp4',
            'title': 'FIFA 14 - E3 2013 Trailer',
            'timestamp': 1370938118,
            'upload_date': '20130611',
            'duration': 82,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_info = self._parse_json(
            js_to_json(self._html_search_regex(
                '(?s)videoObject\s*=\s*({.+?});', webpage, 'video object')),
            video_id)

        formats = []
        for video_url in re.findall(r'var\s+videourl\s*=\s*"([^"]+)"', webpage):
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                formats.append({
                    'url': video_url.replace('de.hls.fra.clipfish.de', 'hls.fra.clipfish.de'),
                    'ext': 'mp4',
                    'format_id': 'hls',
                })
            else:
                formats.append({
                    'url': video_url,
                    'format_id': ext,
                })
        self._sort_formats(formats)

        title = remove_end(self._og_search_title(webpage), ' - Video')
        thumbnail = self._og_search_thumbnail(webpage)
        duration = int_or_none(video_info.get('length'))
        timestamp = parse_iso8601(self._html_search_meta('uploadDate', webpage, 'upload date'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
        }

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json


class RottenTomatoesIE(InfoExtractor):
    _VALID_URL = r'https?://www\.rottentomatoes\.com/m/[^/]+/trailers/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.rottentomatoes.com/m/toy_story_3/trailers/11028566/',
        'info_dict': {
            'id': '11028566',
            'ext': 'mp4',
            'title': 'Toy Story 3',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        params = self._parse_json(
            self._search_regex(r'(?s)RTVideo\(({.+?})\);', webpage, 'player parameters'),
            video_id, transform_source=lambda s: js_to_json(s.replace('window.location.href', '""')))

        formats = []
        if params.get('urlHLS'):
            formats.extend(self._extract_m3u8_formats(
                params['urlHLS'], video_id, ext='mp4',
                entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
        if params.get('urlMP4'):
            formats.append({
                'url': params['urlMP4'],
                'format_id': 'mp4',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'thumbnail': params.get('thumbnailImg'),
        }

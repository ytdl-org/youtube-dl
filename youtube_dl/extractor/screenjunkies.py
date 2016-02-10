from __future__ import unicode_literals

import re
import json

from .common import (
    InfoExtractor,
    ExtractorError,
)

from ..utils import (
    int_or_none,
)

class ScreenJunkiesIE(InfoExtractor):
    _VALID_URL = r'http://www.screenjunkies.com/video/(.+-(?P<id>\d+)|.+)'

    _TESTS = [{
        'url': 'http://www.screenjunkies.com/video/best-quentin-tarantino-movie-2841915',
        'info_dict': {
            'id': '2841915',
            'ext': 'mp4',
            'title': 'Best Quentin Tarantino Movie',
        },
    }, {
        'url': 'http://www.screenjunkies.com/video/honest-trailers-the-dark-knight',
        'info_dict': {
            'id': '2348808',
            'ext': 'mp4',
            'title': "Honest Trailers - 'The Dark Knight'",
        },
    }, {
        'url': 'http://www.screenjunkies.com/video/knocking-dead-ep-1-the-show-so-far-3003285',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if not video_id: # Older urls didn't have the id in them, but we can grab it manually
            webpage = self._download_webpage(url, url)
            video_id = self._html_search_regex(r'src="/embed/(\d+)"', webpage, 'video id')

        webpage = self._download_webpage('http://www.screenjunkies.com/embed/%s' %video_id, video_id)
        video_vars_str = self._html_search_regex(r'embedVars = (\{.+\})\s*</script>', webpage, 'video variables', flags=re.S)
        video_vars = self._parse_json(video_vars_str, video_id)

        # TODO: Figure out required cookies
        if video_vars['subscriptionLevel'] > 0:
            raise ExtractorError('This video requires ScreenJunkiesPlus', expected=True)

        formats = []
        for f in video_vars['media']:
            if not f['mediaPurpose'] == 'play':
                continue

            formats.append({
                'url': f['uri'],
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'tbr': int_or_none(f.get('bitRate')),
                'format': 'mp4',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_vars['contentName'],
            'formats': formats,
            'duration': int_or_none(video_vars.get('videoLengthInSeconds')),
            'thumbnail': video_vars.get('thumbUri'),
            'tags': video_vars['tags'].split(',') if 'tags' in video_vars else [],
        }


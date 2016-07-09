from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    parse_duration,
)


class SSAIE(InfoExtractor):
    _VALID_URL = r'https?://ssa\.nls\.uk/film/(?P<id>\d+)'
    _TEST = {
        'url': 'http://ssa.nls.uk/film/3561',
        'info_dict': {
            'id': '3561',
            'ext': 'flv',
            'title': 'SHETLAND WOOL',
            'description': 'md5:c5afca6871ad59b4271e7704fe50ab04',
            'duration': 900,
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        streamer = self._search_regex(
            r"'streamer'\s*,\S*'(rtmp[^']+)'", webpage, 'streamer')
        play_path = self._search_regex(
            r"'file'\s*,\s*'([^']+)'", webpage, 'file').rpartition('.')[0]

        def search_field(field_name, fatal=False):
            return self._search_regex(
                r'<span\s+class="field_title">%s:</span>\s*<span\s+class="field_content">([^<]+)</span>' % field_name,
                webpage, 'title', fatal=fatal)

        title = unescapeHTML(search_field('Title', fatal=True)).strip('()[]')
        description = unescapeHTML(search_field('Description'))
        duration = parse_duration(search_field('Running time'))
        thumbnail = self._search_regex(
            r"'image'\s*,\s*'([^']+)'", webpage, 'thumbnails', fatal=False)

        return {
            'id': video_id,
            'url': streamer,
            'play_path': play_path,
            'ext': 'flv',
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
        }

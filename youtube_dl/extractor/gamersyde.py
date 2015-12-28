from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    parse_duration,
    remove_start,
)


class GamersydeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamersyde\.com/hqstream_(?P<display_id>[\da-z_]+)-(?P<id>\d+)_[a-z]{2}\.html'
    _TEST = {
        'url': 'http://www.gamersyde.com/hqstream_bloodborne_birth_of_a_hero-34371_en.html',
        'md5': 'f38d400d32f19724570040d5ce3a505f',
        'info_dict': {
            'id': '34371',
            'ext': 'mp4',
            'duration': 372,
            'title': 'Bloodborne - Birth of a hero',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        playlist = self._parse_json(
            self._search_regex(
                r'(?s)playlist: \[({.+?})\]\s*}\);', webpage, 'files'),
            display_id, transform_source=js_to_json)

        formats = []
        for source in playlist['sources']:
            video_url = source.get('file')
            if not video_url:
                continue
            format_id = source.get('label')
            f = {
                'url': video_url,
                'format_id': format_id,
            }
            m = re.search(r'^(?P<height>\d+)[pP](?P<fps>\d+)fps', format_id)
            if m:
                f.update({
                    'height': int(m.group('height')),
                    'fps': int(m.group('fps')),
                })
            formats.append(f)
        self._sort_formats(formats)

        title = remove_start(playlist['title'], '%s - ' % video_id)
        thumbnail = playlist.get('image')
        duration = parse_duration(self._search_regex(
            r'Length:</label>([^<]+)<', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }

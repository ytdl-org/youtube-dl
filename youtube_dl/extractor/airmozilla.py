# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    parse_iso8601,
)


class AirMozillaIE(InfoExtractor):
    _VALID_URL = r'https?://air\.mozilla\.org/(?P<id>[0-9a-z-]+)/?'
    _TEST = {
        'url': 'https://air.mozilla.org/privacy-lab-a-meetup-for-privacy-minded-people-in-san-francisco/',
        'md5': '2e3e7486ba5d180e829d453875b9b8bf',
        'info_dict': {
            'id': '6x4q2w',
            'ext': 'mp4',
            'title': 'Privacy Lab - a meetup for privacy minded people in San Francisco',
            'thumbnail': r're:https?://vid\.ly/(?P<id>[0-9a-z-]+)/poster',
            'description': 'Brings together privacy professionals and others interested in privacy at for-profits, non-profits, and NGOs in an effort to contribute to the state of the ecosystem...',
            'timestamp': 1422487800,
            'upload_date': '20150128',
            'location': 'SFO Commons',
            'duration': 3780,
            'view_count': int,
            'categories': ['Main', 'Privacy'],
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._html_search_regex(r'//vid.ly/(.*?)/embed', webpage, 'id')

        embed_script = self._download_webpage('https://vid.ly/{0}/embed'.format(video_id), video_id)
        jwconfig = self._search_regex(r'\svar jwconfig = (\{.*?\});\s', embed_script, 'metadata')
        metadata = self._parse_json(jwconfig, video_id)

        formats = [{
            'url': source['file'],
            'ext': source['type'],
            'format_id': self._search_regex(r'&format=(.*)$', source['file'], 'video format'),
            'format': source['label'],
            'height': int(source['label'].rstrip('p')),
        } for source in metadata['playlist'][0]['sources']]
        self._sort_formats(formats)

        view_count = int_or_none(self._html_search_regex(
            r'Views since archived: ([0-9]+)',
            webpage, 'view count', fatal=False))
        timestamp = parse_iso8601(self._html_search_regex(
            r'<time datetime="(.*?)"', webpage, 'timestamp', fatal=False))
        duration = parse_duration(self._search_regex(
            r'Duration:\s*(\d+\s*hours?\s*\d+\s*minutes?)',
            webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'url': self._og_search_url(webpage),
            'display_id': display_id,
            'thumbnail': metadata['playlist'][0].get('image'),
            'description': self._og_search_description(webpage),
            'timestamp': timestamp,
            'location': self._html_search_regex(r'Location: (.*)', webpage, 'location', default=None),
            'duration': duration,
            'view_count': view_count,
            'categories': re.findall(r'<a href=".*?" class="channel">(.*?)</a>', webpage),
        }

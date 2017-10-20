# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    float_or_none,
    mimetype2ext,
)


class OnionStudiosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onionstudios\.com/(?:video(?:s/[^/]+-|/)|embed\?.*\bid=)(?P<id>\d+)(?!-)'

    _TESTS = [{
        'url': 'http://www.onionstudios.com/videos/hannibal-charges-forward-stops-for-a-cocktail-2937',
        'md5': '719d1f8c32094b8c33902c17bcae5e34',
        'info_dict': {
            'id': '2937',
            'ext': 'mp4',
            'title': 'Hannibal charges forward, stops for a cocktail',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'The A.V. Club',
            'uploader_id': 'the-av-club',
        },
    }, {
        'url': 'http://www.onionstudios.com/embed?id=2855&autoplay=true',
        'only_matching': True,
    }, {
        'url': 'http://www.onionstudios.com/video/6139.json',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'(?s)<(?:iframe|bulbs-video)[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?onionstudios\.com/(?:embed.+?|video/\d+\.json))\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_json(
            'http://www.onionstudios.com/video/%s.json' % video_id, video_id)

        title = video_data['title']

        formats = []
        for source in video_data.get('sources', []):
            source_url = source.get('url')
            if not source_url:
                continue
            ext = mimetype2ext(source.get('content_type')) or determine_ext(source_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
            else:
                tbr = int_or_none(source.get('bitrate'))
                formats.append({
                    'format_id': ext + ('-%d' % tbr if tbr else ''),
                    'url': source_url,
                    'width': int_or_none(source.get('width')),
                    'tbr': tbr,
                    'ext': ext,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': video_data.get('poster_url'),
            'uploader': video_data.get('channel_name'),
            'uploader_id': video_data.get('channel_slug'),
            'duration': float_or_none(video_data.get('duration', 1000)),
            'tags': video_data.get('tags'),
            'formats': formats,
        }

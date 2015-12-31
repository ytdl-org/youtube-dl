# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class AnimalPlanetIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?animalplanet\.com/([^/]+/)*(?P<id>[^/\?#]+)'
    _TESTS = [{
        'url': 'http://www.animalplanet.com/tv-shows/i-shouldnt-be-alive/videos/dog-saves-injured-owner/',
        'info_dict': {
            'id': '10608',
            'ext': 'mp4',
            'title': 'Dog Saves Injured Owner',
            'description': 'A world class athlete is put to the test when she falls into a canyon and breaks her hip. Her only companion is her dog, Taz, who is on a mission to save her!',
            'upload_date': '20100410',
            'timestamp': 1270857727,
            'duration': 220,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.animalplanet.com/longfin-eels-maneaters/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_data = self._parse_json(self._search_regex(
            r'initialVideoData\s*=\s*({.+?});',
            webpage, 'initialVideoData'), display_id)['playlist'][0]

        return {
            'id': compat_str(video_data['id']),
            'display_id': display_id,
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailURL'),
            'duration': parse_duration(video_data.get('video_length')),
            'timestamp': parse_iso8601(video_data.get('publishedDate')),
            'formats': self._extract_m3u8_formats(
                video_data['src'], display_id, 'mp4',
                'm3u8_native', m3u8_id='hls')
        }

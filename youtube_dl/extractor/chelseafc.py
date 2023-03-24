# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import unified_timestamp, parse_duration


class ChelseafcIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chelseafc\.com(?:/[a-z]+)?/video/(?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)'
    _TESTS = [{
        'url': 'https://www.chelseafc.com/en/video/full-match-chelsea-2-2-everton',
        'md5': '0f7cd37de17faa71566bfd9074315c85',
        'info_dict': {
            'id': 'full-match-chelsea-2-2-everton',
            'ext': 'mp4',
            'title': 'Full Match: Chelsea 2-2 Everton',
            'description': 'Full match highlights from Chelsea\'s 2-2 Premier League draw with Everton at Stamford Bridge. ',
            'duration': 2842.0,
            'timestamp': 1679184000,
            'upload_date': '20230319',
            'thumbnail': r're:https?://.*\.png'
        }
    },
        {
        'url': 'https://www.chelseafc.com/en/video/manchester-city-vs-chelsea-2-0-or-highlights-or-efl-cup',
        'md5': '01078658408ee98b1cf286d3b8f4b7ca',
        'info_dict': {
            'id': 'manchester-city-vs-chelsea-2-0-or-highlights-or-efl-cup',
            'ext': 'mp4',
            'title': 'Manchester City 2-0 Chelsea | Highlights | EFL Cup',
            'description': 'Highlights from our EFL Cup match against Man City.',
            'duration': 120.0,
            'timestamp': 1668042000,
            'upload_date': '20221110',
            'thumbnail': r're:https?://.*\.jpg'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_details_div = self._search_regex(
            r'(<div[^>]*\sdata-component\s*=\s*(?:"|\')\s*VideoDetails\s*(?:"|\')[^>]*>)',
            webpage,
            'div'
        )
        raw_data = self._html_search_regex(
            r'<div[^>]*\sdata-props\s*=\s*(?:"|\')\s*([^"\']*)\s*(?:"|\')[^>]*>',
            video_details_div,
            'data'
        )

        data = json.loads(raw_data)['videoDetail']

        manifest_url = data['signedUrl']
        formats = self._extract_m3u8_formats(manifest_url, video_id, 'mp4')

        title = data['title']
        descripiton = data['description']
        timestamp = unified_timestamp(data['releaseDate'])
        duration = parse_duration(data['duration'])
        tags = [tag['title'] for tag in data['tags']]
        thumbnail = data['image']['file']['url']

        return {
            'id': video_id,
            'title': title,
            'description': descripiton,
            'formats': formats,
            'duration': duration,
            'timestamp': timestamp,
            'tags': tags,
            'thumbnail': thumbnail
        }

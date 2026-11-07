# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class ChelseafcIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chelseafc\.com(?:/[a-z]+)?/video/(?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)'
    _TESTS = [{
        'url': 'https://www.chelseafc.com/en/video/full-match-chelsea-2-2-everton',
        'md5': '2fda617911b7148a2a19bec55b75d30a',
        'info_dict': {
            'id': 'full-match-chelsea-2-2-everton',
            'ext': 'mp4',
            'title': 'Full Match: Chelsea 2-2 Everton',
            'description': 'Full match highlights from Chelsea\'s 2-2 Premier League draw with Everton at Stamford Bridge.',
            'duration': 2842.0,
            'timestamp': 1679184000,
            'tags': ['Premier League', 'Everton', 'Video and article choice'],
            'upload_date': '20230319',
            'thumbnail': r're:https?://.*\.png'
        }
    },
        {
        'url': 'https://www.chelseafc.com/en/video/manchester-city-vs-chelsea-2-0-or-highlights-or-efl-cup',
        'md5': '2905365c3c9cf4612f303fbb99c2f4ca',
        'info_dict': {
            'id': 'manchester-city-vs-chelsea-2-0-or-highlights-or-efl-cup',
            'ext': 'mp4',
            'title': 'Manchester City 2-0 Chelsea | Highlights | EFL Cup',
            'description': 'Highlights from our EFL Cup match against Man City.',
            'duration': 120.0,
            'timestamp': 1668042000,
            'upload_date': '20221110',
            'tags': ['Highlights', 'League Cup', 'Manchester City'],
            'thumbnail': r're:https?://.*\.jpg'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_details_div = self._search_regex(
            r'(<div\s[^>]*\bdata-component\s*=\s*(?:"|\')\s*VideoDetails\s*(?:"|\')[^>]*>)',
            webpage,
            'div'
        )
        raw_data = self._html_search_regex(
            r'<div[^>]*\sdata-props\s*=\s*(?:"|\')\s*([^"\']*)\s*(?:"|\')[^>]*>',
            video_details_div,
            'data'
        )

        data = self._parse_json(raw_data, video_id)
        manifest_url = data['videoDetail']['signedUrl']

        data = data['videoDetail']

        title = data['title']

        formats = self._extract_m3u8_formats(manifest_url, video_id, 'mp4')
        self._sort_formats(formats)

        txt_or_none = lambda x: x.strip() or None

        return {
            'id': video_id,
            'title': title,
            'description': txt_or_none(data.get('description')),
            'formats': formats,
            'duration': parse_duration(data.get('duration')),
            'timestamp': unified_timestamp(data.get('releaseDate')),
            'tags': traverse_obj(data, ('tags', Ellipsis, 'title'), expected_type=txt_or_none),
            'thumbnail': traverse_obj(data, ('image', 'file', 'url'), expected_type=url_or_none),
        }

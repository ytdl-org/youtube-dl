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
        'url': 'https://www.chelseafc.com/en/video/training-ahead-of-brentford-27-10-2023',
        'info_dict': {
            'id': 'training-ahead-of-brentford-27-10-2023',
            'ext': 'mp4',
            'title': 'Training ahead of Brentford ⚽️',
            'description': 'Watch another set of intense training sessions ahead of our London derby against Brentford this Saturday...',
            'duration': 481.0,
            'timestamp': 1698411300,
            'tags': ['Brentford', 'Kit Launch'],
            'upload_date': '20231027',
            'thumbnail': r're:https?://.*.jpg'
        }
    },
        {
        'url': 'https://www.chelseafc.com/en/video/pochettinos-press-conference-27-10-2023',
        'info_dict': {
            'id': 'pochettinos-press-conference-27-10-2023',
            'ext': 'mp4',
            'title': '🎙️ Pochettino\'s press conference',
            'description': 'Every word of Mauricio\'s press conference, ahead of Saturday\'s Premier League match against Brentford at Stamford Bridge...',
            'duration': 729.0,
            'timestamp': 1698410700,
            'tags': ['Press Conferences', 'Mauricio Pochettino', 'Brentford', 'Premier League'],
            'upload_date': '20231027',
            'thumbnail': r're:https?://.*.jpg'
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
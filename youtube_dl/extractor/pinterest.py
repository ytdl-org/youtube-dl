# coding: utf-8
from .common import InfoExtractor
from ..utils import (
    js_to_json,
    str_or_none,
    try_get,
    determine_ext,
)


class PinterestIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pinterest\.com/pin/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.pinterest.com/pin/705939310335590838/',
        'md5': 'cec64cd13da298ad27e17d0c36ffec7b',
        'info_dict': {
            'description': 'Ad: Floating lanterns in the night sky. Launching Sky Lantern. Yee Peng Festival, Loy Krathong celebration.',
            'ext': 'mp4',
            'id': '705939310335590838',
            'title': 'Floating Lanterns in the Night Stock Footage Video (100% Royalty-free) 1021682980 | Shutterstock',
            'uploader': 'UF | Unique Footages',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data = self._parse_video_data(webpage, video_id)
        formats = self._extract_formats(try_get(data, lambda x: x['videos']['video_list']) or {}, video_id)

        return {
            'id': video_id,
            'title': str_or_none(data.get('title')),
            'description': str_or_none(data.get('closeup_unified_description')),
            'uploader': try_get(data, lambda x: x['closeup_attribution']['full_name']),
            'formats': formats,
        }

    def _parse_video_data(self, webpage, video_id):
        script = self._search_regex(
            r'<script[^>]+id=(["\'])initial-state\1[^>]*>(?P<json>[^<]+)',
            webpage, 'video data', group='json')

        return try_get(self._parse_json(script, video_id, transform_source=js_to_json),
                       lambda x: x['resourceResponses'][0]['response']['data']) or {}

    def _extract_formats(self, video_list, video_id):
        formats = []
        for format_id, format_data in video_list.items():
            url = format_data.get('url')
            if 'm3u8' == determine_ext(url):
                formats.extend(self._extract_m3u8_formats(url, video_id, 'mp4', 'm3u8_native', m3u8_id=format_id))
            else:
                formats.append({
                    'duration': format_data.get('duration'),
                    'format_id': format_id,
                    'height': format_data.get('height'),
                    'thumbnail': format_data.get('thumbnail'),
                    'url': url,
                    'width': format_data.get('width'),
                })
        self._sort_formats(formats)

        return formats

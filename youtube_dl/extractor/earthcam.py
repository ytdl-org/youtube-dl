# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urljoin,
    int_or_none,
    url_or_none,
    try_get,
)


class EarthCamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?earthcam\.com/.*\?.*cam=(?P<id>\w+)'
    _TEST = {
        'url': 'https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo1',
        'info_dict': {
            'id': 'tsrobo1',
            'ext': 'mp4',
            'title': 'Times Square, NYC',
            'description': 'EarthCam  brings you an HD, panoramic view of Times Square looking up, down, and across 7th Avenue and Broadway. See why Times Square is called the "Crossroads of the World!"',
            'view_count': int,
            'is_live': True,
            'thumbnail': r're:^https?://.*\.(jpg|png)$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_str = self._search_regex(r'var\s+json_base\s*=\s*(?P<jstr>{\s*"cam"\s*:\s*{.*}.*});', webpage, 'jstr')
        json_base = self._parse_json(json_str, video_id)
        video_info = try_get(json_base, lambda x: x['cam'][video_id], dict) or {}
        title = video_info.get("long_title")
        description = video_info.get("description")
        thumbnail = video_info.get("thumbimage")
        view_count = int_or_none(video_info.get("streamviews"))
        domain = video_info.get("html5_streamingdomain")
        path = video_info.get("html5_streampath")
        m3u8_url = urljoin(domain, path)

        return {
            'id': video_id,
            'formats': self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', 'm3u8_native'),
            'title': title or self._og_search_title(webpage),
            'description': description or self._og_search_description(webpage),
            'view_count': view_count,
            'is_live': True,
            'thumbnail': url_or_none(thumbnail),
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urljoin,
)


class EarthCamsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?earthcam\.com/.*?cam=(?P<id>\w+)'
    _TEST = {
        'url': 'https://www.earthcam.com/usa/newyork/timessquare/?cam=tsrobo1',
        'info_dict': {
            'id': 'tsrobo1',
            'ext': 'mp4',
            'title': 'Times Square, NYC',
            'description': 'EarthCam  brings you an HD, panoramic view of Times Square looking up, down, and across 7th Avenue and Broadway. See why Times Square is called the "Crossroads of the World!"',
            'view_count': int,
            'is_live': True,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_str = self._search_regex(r'var\sjson_base\s*=\s*(?P<jstr>{.*});', webpage, 'jstr')
        json_base = self._parse_json(json_str, video_id)

        title = json_base["cam"][video_id]["long_title"]
        description = json_base["cam"][video_id]["description"]
        thumbnail = json_base["cam"][video_id]["thumbimage"]
        view_count = int(json_base["cam"][video_id]["streamviews"])

        domain = json_base["cam"][video_id]["html5_streamingdomain"]
        path = json_base["cam"][video_id]["html5_streampath"]
        m3u8_url = urljoin(domain, path)

        return {
            'id': video_id,
            'formats': self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', 'm3u8_native'),
            'title': title,
            'description': description,
            'view_count': view_count,
            'is_live': True,
            'thumbnail': thumbnail,
        }

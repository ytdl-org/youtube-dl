# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urljoin,
    int_or_none,
    url_or_none,
    try_get,
    js_to_json,
)


class EarthCamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?earthcam\.com/.*\?.*cam=(?P<id>\w+)'
    _TESTS = [{
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
    }, {
        'url': 'https://www.earthcam.com/usa/louisiana/neworleans/bourbonstreet/?cam=catsmeowkaraoke',
        'info_dict': {
            'id': 'catsmeowkaraoke',
            'ext': 'mp4',
            'title': 'New Orleans, LA',
            'description': 'Get a front row seat to all the wild and crazy stage performances happening at the Cat\'s Meow Karaoke Bar! Over the years, thousands of guests have enjoyed their moment singing in the spotlight at this popular local spot!',
            'view_count': int,
            'is_live': True,
            'thumbnail': r're:^https?://.*\.(jpg|png)$',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_str = self._html_search_regex(r'var\s+json_base\s*=\s*(?P<json_str>{\s*"cam"\s*:\s*{.*}.*});', webpage, 'json', group='json_str', default='{}')
        json_base = self._parse_json(js_to_json(json_str), video_id)

        video_info = json_base['cam'][video_id]
        domain = video_info['html5_streamingdomain']
        path = video_info['html5_streampath']
        m3u8_url = urljoin(domain, path)
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', 'm3u8_native')

        title = video_info.get('long_title') or self._og_search_title(webpage)
        description = video_info.get('description') or self._og_search_description(webpage)
        thumbnail = url_or_none(video_info.get('thumbimage')) or self._og_search_thumbnail(webpage)
        view_count = int_or_none(video_info.get("streamviews"))
        
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'view_count': view_count,
            'is_live': True,
            'thumbnail': thumbnail,
        }

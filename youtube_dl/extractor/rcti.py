# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RCTIplusIE(InfoExtractor):
    _VALID_URL = r'https://www\.rctiplus\.com/programs/\d+?/.*?/episode/(?P<id>\d+)/.*'
    _TEST = {
        'url': 'https://www.rctiplus.com/programs/540/upin-ipin/episode/5642/esok-puasa-upin-ipin-ep1',
        'md5': 'e9b7c88101aab04d9115e2718dae7260',
        'info_dict': {
            'id': '5642',
            'title': 'Esok Puasa - Upin & Ipin Ep.1',
            'ext': 'm3u8',
        },
        'params': {
            'format': 'bestvideo, bestaudio',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)

        auth_key = self._search_regex(
            r'\'Authorization\':"(?P<auth>[^"]+)"', webpage, 'auth-key')
        request_url = ('https://api.rctiplus.com/api/v1/episode/' + video_id
                       + '/url?appierid=.1')
        json = self._download_json(
            request_url, video_id, headers={'Authorization': auth_key})
        video_url = json.get('data').get('url')

        formats = self._extract_m3u8_formats(video_url, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TheAtlanticIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?theatlantic\.com/video/index/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.theatlantic.com/video/index/477918/capture-a-unified-theory-on-mental-health/',
        'md5': '',
        'info_dict': {
            'id': '477918',
            'ext': 'mp4',
            'title': 'Are All Mental Illnesses Related?',
            'description': 'Depression, anxiety, overeating, addiction, and all other mental disorders share a common mechanism.',
            'timestamp': 1460490952,
            'uploader': 'TheAtlantic',
            'upload_date': '20160412',
            'uploader_id': '29913724001',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['BrightcoveLegacy'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return {
            '_type': 'url_transparent',
            'url': self._html_search_meta('twitter:player', webpage),
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'ie_key': 'BrightcoveLegacy',
        }

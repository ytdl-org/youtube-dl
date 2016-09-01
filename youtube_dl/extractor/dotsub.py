from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
)


class DotsubIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dotsub\.com/view/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://dotsub.com/view/9c63db2a-fa95-4838-8e6e-13deafe47f09',
        'md5': '21c7ff600f545358134fea762a6d42b6',
        'info_dict': {
            'id': '9c63db2a-fa95-4838-8e6e-13deafe47f09',
            'ext': 'flv',
            'title': 'MOTIVATION - "It\'s Possible" Best Inspirational Video Ever',
            'description': 'md5:41af1e273edbbdfe4e216a78b9d34ac6',
            'thumbnail': 're:^https?://dotsub.com/media/9c63db2a-fa95-4838-8e6e-13deafe47f09/p',
            'duration': 198,
            'uploader': 'liuxt',
            'timestamp': 1385778501.104,
            'upload_date': '20131130',
            'view_count': int,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_json(
            'https://dotsub.com/api/media/%s/metadata' % video_id, video_id)
        video_url = info.get('mediaURI')

        if not video_url:
            webpage = self._download_webpage(url, video_id)
            video_url = self._search_regex(
                [r'<source[^>]+src="([^"]+)"', r'"file"\s*:\s*\'([^\']+)'],
                webpage, 'video url')

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': info['title'],
            'description': info.get('description'),
            'thumbnail': info.get('screenshotURI'),
            'duration': int_or_none(info.get('duration'), 1000),
            'uploader': info.get('user'),
            'timestamp': float_or_none(info.get('dateCreated'), 1000),
            'view_count': int_or_none(info.get('numberOfViews')),
        }

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
)


class DotsubIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dotsub\.com/view/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://dotsub.com/view/aed3b8b2-1889-4df5-ae63-ad85f5572f27',
        'md5': '0914d4d69605090f623b7ac329fea66e',
        'info_dict': {
            'id': 'aed3b8b2-1889-4df5-ae63-ad85f5572f27',
            'ext': 'flv',
            'title': 'Pyramids of Waste (2010), AKA The Lightbulb Conspiracy - Planned obsolescence documentary',
            'description': 'md5:699a0f7f50aeec6042cb3b1db2d0d074',
            'thumbnail': 're:^https?://dotsub.com/media/aed3b8b2-1889-4df5-ae63-ad85f5572f27/p',
            'duration': 3169,
            'uploader': '4v4l0n42',
            'timestamp': 1292248482.625,
            'upload_date': '20101213',
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

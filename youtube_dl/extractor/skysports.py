# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SkySportsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?skysports\.com/watch/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.skysports.com/watch/video/10328419/bale-its-our-time-to-shine',
        'md5': 'c44a1db29f27daf9a0003e010af82100',
        'info_dict': {
            'id': '10328419',
            'ext': 'flv',
            'title': 'Bale: Its our time to shine',
            'description': 'md5:9fd1de3614d525f5addda32ac3c482c9',
        },
        'add_ie': ['Ooyala'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'ooyala:%s' % self._search_regex(
                r'data-video-id="([^"]+)"', webpage, 'ooyala id'),
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'ie_key': 'Ooyala',
        }

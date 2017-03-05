# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import strip_or_none


class SkySportsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?skysports\.com/watch/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.skysports.com/watch/video/10328419/bale-its-our-time-to-shine',
        'md5': '77d59166cddc8d3cb7b13e35eaf0f5ec',
        'info_dict': {
            'id': '10328419',
            'ext': 'mp4',
            'title': 'Bale: It\'s our time to shine',
            'description': 'md5:e88bda94ae15f7720c5cb467e777bb6d',
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
            'description': strip_or_none(self._og_search_description(webpage)),
            'ie_key': 'Ooyala',
        }

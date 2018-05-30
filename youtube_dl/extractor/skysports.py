# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    smuggle_url,
    strip_or_none,
    urljoin,
)


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
        video_data = extract_attributes(self._search_regex(
            r'(<div.+?class="sdc-article-video__media-ooyala"[^>]+>)', webpage, 'video data'))

        video_url = 'ooyala:%s' % video_data['data-video-id']
        if video_data.get('data-token-required') == 'true':
            token_fetch_options = self._parse_json(video_data.get('data-token-fetch-options', '{}'), video_id, fatal=False) or {}
            token_fetch_url = token_fetch_options.get('url')
            if token_fetch_url:
                embed_token = self._download_webpage(urljoin(url, token_fetch_url), video_id, fatal=False)
                if embed_token:
                    video_url = smuggle_url(video_url, {'embed_token': embed_token.strip('"')})

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': strip_or_none(self._og_search_description(webpage)),
            'ie_key': 'Ooyala',
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    smuggle_url,
    strip_or_none,
    urljoin,
)


class SkyBaseIE(InfoExtractor):
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_data = extract_attributes(self._search_regex(
            r'(<div.+?class="[^"]*sdc-article-video__media-ooyala[^"]*"[^>]+>)',
            webpage, 'video data'))

        video_url = 'ooyala:%s' % video_data['data-video-id']
        if video_data.get('data-token-required') == 'true':
            token_fetch_options = self._parse_json(video_data.get(
                'data-token-fetch-options', '{}'), video_id, fatal=False) or {}
            token_fetch_url = token_fetch_options.get('url')
            if token_fetch_url:
                embed_token = self._download_webpage(urljoin(
                    url, token_fetch_url), video_id, fatal=False)
                if embed_token:
                    video_url = smuggle_url(
                        video_url, {'embed_token': embed_token.strip('"')})

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': strip_or_none(self._og_search_description(webpage)),
            'ie_key': 'Ooyala',
        }


class SkySportsIE(SkyBaseIE):
    _VALID_URL = r'https?://(?:www\.)?skysports\.com/watch/video/([^/]+/)*(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.skysports.com/watch/video/10328419/bale-its-our-time-to-shine',
        'md5': '77d59166cddc8d3cb7b13e35eaf0f5ec',
        'info_dict': {
            'id': 'o3eWJnNDE6l7kfNO8BOoBlRxXRQ4ANNQ',
            'ext': 'mp4',
            'title': 'Bale: It\'s our time to shine',
            'description': 'md5:e88bda94ae15f7720c5cb467e777bb6d',
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'https://www.skysports.com/watch/video/sports/f1/12160544/abu-dhabi-gp-the-notebook',
        'only_matching': True,
    }, {
        'url': 'https://www.skysports.com/watch/video/tv-shows/12118508/rainford-brent-how-ace-programme-helps',
        'only_matching': True,
    }]


class SkyNewsIE(SkyBaseIE):
    _VALID_URL = r'https?://news\.sky\.com/video/[0-9a-z-]+-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://news.sky.com/video/russian-plane-inspected-after-deadly-fire-11712962',
        'md5': 'd6327e581473cea9976a3236ded370cd',
        'info_dict': {
            'id': '1ua21xaDE6lCtZDmbYfl8kwsKLooJbNM',
            'ext': 'mp4',
            'title': 'Russian plane inspected after deadly fire',
            'description': 'The Russian Investigative Committee has released video of the wreckage of a passenger plane which caught fire near Moscow.',
        },
        'add_ie': ['Ooyala'],
    }

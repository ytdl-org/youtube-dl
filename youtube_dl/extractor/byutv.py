from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class BYUtvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?byutv\.org/watch/(?!event/)(?P<id>[0-9a-f-]+)(?:/(?P<display_id>[^/?#&]+))?'
    _TESTS = [{
        'url': 'http://www.byutv.org/watch/6587b9a3-89d2-42a6-a7f7-fd2f81840a7d/studio-c-season-5-episode-5',
        'info_dict': {
            'id': '6587b9a3-89d2-42a6-a7f7-fd2f81840a7d',
            'display_id': 'studio-c-season-5-episode-5',
            'ext': 'mp4',
            'title': 'Season 5 Episode 5',
            'description': 'md5:e07269172baff037f8e8bf9956bc9747',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 1486.486,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://www.byutv.org/watch/6587b9a3-89d2-42a6-a7f7-fd2f81840a7d',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)
        episode_code = self._search_regex(
            r'(?s)episode:(.*?\}),\s*\n', webpage, 'episode information')

        ep = self._parse_json(
            episode_code, display_id, transform_source=lambda s:
            re.sub(r'(\n\s+)([a-zA-Z]+):\s+\'(.*?)\'', r'\1"\2": "\3"', s))

        if ep['providerType'] != 'Ooyala':
            raise ExtractorError('Unsupported provider %s' % ep['provider'])

        return {
            '_type': 'url_transparent',
            'ie_key': 'Ooyala',
            'url': 'ooyala:%s' % ep['providerId'],
            'id': video_id,
            'display_id': display_id,
            'title': ep['title'],
            'description': ep.get('description'),
            'thumbnail': ep.get('imageThumbnail'),
        }


class BYUtvEventIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?byutv\.org/watch/event/(?P<id>[0-9a-f-]+)'
    _TEST = {
        'url': 'http://www.byutv.org/watch/event/29941b9b-8bf6-48d2-aebf-7a87add9e34b',
        'info_dict': {
            'id': '29941b9b-8bf6-48d2-aebf-7a87add9e34b',
            'ext': 'mp4',
            'title': 'Toledo vs. BYU (9/30/16)',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        ooyala_id = self._search_regex(
            r'providerId\s*:\s*(["\'])(?P<id>(?:(?!\1).)+)\1',
            webpage, 'ooyala id', group='id')

        title = self._search_regex(
            r'class=["\']description["\'][^>]*>\s*<h1>([^<]+)</h1>', webpage,
            'title').strip()

        return {
            '_type': 'url_transparent',
            'ie_key': 'Ooyala',
            'url': 'ooyala:%s' % ooyala_id,
            'id': video_id,
            'title': title,
        }

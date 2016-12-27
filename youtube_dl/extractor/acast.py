# coding: utf-8
from __future__ import unicode_literals

import re
import functools

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_iso8601,
    OnDemandPagedList,
)


class ACastIE(InfoExtractor):
    IE_NAME = 'acast'
    _VALID_URL = r'https?://(?:www\.)?acast\.com/(?P<channel>[^/]+)/(?P<id>[^/#?]+)'
    _TESTS = [{
        # test with one bling
        'url': 'https://www.acast.com/condenasttraveler/-where-are-you-taipei-101-taiwan',
        'md5': 'ada3de5a1e3a2a381327d749854788bb',
        'info_dict': {
            'id': '57de3baa-4bb0-487e-9418-2692c1277a34',
            'ext': 'mp3',
            'title': '"Where Are You?": Taipei 101, Taiwan',
            'timestamp': 1196172000,
            'upload_date': '20071127',
            'description': 'md5:a0b4ef3634e63866b542e5b1199a1a0e',
            'duration': 211,
        }
    }, {
        # test with multiple blings
        'url': 'https://www.acast.com/sparpodcast/2.raggarmordet-rosterurdetforflutna',
        'md5': '55c0097badd7095f494c99a172f86501',
        'info_dict': {
            'id': '2a92b283-1a75-4ad8-8396-499c641de0d9',
            'ext': 'mp3',
            'title': '2. Raggarmordet - Röster ur det förflutna',
            'timestamp': 1477346700,
            'upload_date': '20161024',
            'description': 'md5:4f81f6d8cf2e12ee21a321d8bca32db4',
            'duration': 2797,
        }
    }]

    def _real_extract(self, url):
        channel, display_id = re.match(self._VALID_URL, url).groups()
        cast_data = self._download_json(
            'https://embed.acast.com/api/acasts/%s/%s' % (channel, display_id), display_id)
        return {
            'id': compat_str(cast_data['id']),
            'display_id': display_id,
            'url': [b['audio'] for b in cast_data['blings'] if b['type'] == 'BlingAudio'][0],
            'title': cast_data['name'],
            'description': cast_data.get('description'),
            'thumbnail': cast_data.get('image'),
            'timestamp': parse_iso8601(cast_data.get('publishingDate')),
            'duration': int_or_none(cast_data.get('duration')),
        }


class ACastChannelIE(InfoExtractor):
    IE_NAME = 'acast:channel'
    _VALID_URL = r'https?://(?:www\.)?acast\.com/(?P<id>[^/#?]+)'
    _TEST = {
        'url': 'https://www.acast.com/condenasttraveler',
        'info_dict': {
            'id': '50544219-29bb-499e-a083-6087f4cb7797',
            'title': 'Condé Nast Traveler Podcast',
            'description': 'md5:98646dee22a5b386626ae31866638fbd',
        },
        'playlist_mincount': 20,
    }
    _API_BASE_URL = 'https://www.acast.com/api/'
    _PAGE_SIZE = 10

    @classmethod
    def suitable(cls, url):
        return False if ACastIE.suitable(url) else super(ACastChannelIE, cls).suitable(url)

    def _fetch_page(self, channel_slug, page):
        casts = self._download_json(
            self._API_BASE_URL + 'channels/%s/acasts?page=%s' % (channel_slug, page),
            channel_slug, note='Download page %d of channel data' % page)
        for cast in casts:
            yield self.url_result(
                'https://www.acast.com/%s/%s' % (channel_slug, cast['url']),
                'ACast', cast['id'])

    def _real_extract(self, url):
        channel_slug = self._match_id(url)
        channel_data = self._download_json(
            self._API_BASE_URL + 'channels/%s' % channel_slug, channel_slug)
        entries = OnDemandPagedList(functools.partial(
            self._fetch_page, channel_slug), self._PAGE_SIZE)
        return self.playlist_result(entries, compat_str(
            channel_data['id']), channel_data['name'], channel_data.get('description'))

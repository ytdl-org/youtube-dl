# coding: utf-8
from __future__ import unicode_literals

import re
import functools

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    clean_html,
    float_or_none,
    int_or_none,
    js_to_json,
    try_get,
    unified_timestamp,
    OnDemandPagedList,
)


class ACastIE(InfoExtractor):
    IE_NAME = 'acast'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:(?:embed|www)\.)?acast\.com/|
                            play\.acast\.com/s/
                        )
                        (?P<channel>[^/]+)/(?P<id>[^/#?]+)
                    '''
    _TESTS = [{
        'url': 'https://www.acast.com/sparpodcast/2.raggarmordet-rosterurdetforflutna',
        'md5': 'f5598f3ad1e4776fed12ec1407153e4b',
        'info_dict': {
            'id': '2a92b283-1a75-4ad8-8396-499c641de0d9',
            'ext': 'mp3',
            'title': '2. Raggarmordet - Röster ur det förflutna',
            'description': 'md5:a992ae67f4d98f1c0141598f7bebbf67',
            'timestamp': 1477346700,
            'upload_date': '20161024',
            'duration': 2766.0,
            'creator': 'Anton Berg & Martin Johnson',
            'series': 'Spår',
            'episode': '2. Raggarmordet - Röster ur det förflutna',
        }
    }, {
        'url': 'https://play.acast.com/s/spraktalk/ap-120185',
        'md5': 'dfccc97aaa43976028362c60101f938f',
        'info_dict': {
            'id': 'ap-120185',
            'ext': 'mp3',
            'title': 'Tysk: Likere norsk enn du tror!',
            'description': 'md5:72d161967fc635cd1c839c8307843995',
            'timestamp': 1606190415,
            'upload_date': '20201124',
            'duration': 1665.0,
            'creator': 'Aftenposten',
            'series': 'Språktalk',
            'episode': 'Tysk: Likere norsk enn du tror!',
        }
    }, {
        'url': 'http://embed.acast.com/adambuxton/ep.12-adam-joeschristmaspodcast2015',
        'only_matching': True,
    }, {
        'url': 'https://play.acast.com/s/sparpodcast/2a92b283-1a75-4ad8-8396-499c641de0d9',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        id = self._match_id(url)
        webpage = self._download_webpage(url, id)
        player = self._parse_json(self._search_regex(
            r'<script[^>]*>\s*window\.__INITIAL__STATE__\s*=\s*({.+});</script',
            webpage, 'player', default='{}'), id, transform_source=js_to_json)
        for player_key in player['feeder'].keys():
            if "Show:" in player_key:
                break;
        show_data = player['feeder'][player_key]

        channel, display_id = re.match(self._VALID_URL, url).groups()
        s = self._download_json(
            'https://feeder.acast.com/api/v1/shows/%s/episodes/%s' % (channel, display_id),
            display_id)
        media_url = s['url']

        title = s['title']
        return {
            'id': compat_str(s['id']),
            'display_id': display_id,
            'url': media_url,
            'title': title,
            'description': clean_html(s.get('description')),
            'thumbnail': s.get('image'),
            'timestamp': unified_timestamp(s.get('publishDate')),
            'duration': float_or_none(s.get('duration')),
            'filesize': int_or_none(s.get('contentLength')),
            'creator': show_data.get('author').strip(), # try_get(cast_data, lambda x: x['show']['author'], compat_str),
            'series': show_data.get('title').strip(), # try_get(cast_data, lambda x: x['show']['name'], compat_str),
            'season_number': int_or_none(s.get('season')),
            'episode': title,
            'episode_number': int_or_none(s.get('episode')),
        }


class ACastChannelIE(InfoExtractor):
    IE_NAME = 'acast:channel'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?acast\.com/|
                            play\.acast\.com/s/
                        )
                        (?P<id>[^/#?]+)
                    '''
    _TESTS = [{
        'url': 'https://www.acast.com/todayinfocus',
        'info_dict': {
            'id': '4efc5294-5385-4847-98bd-519799ce5786',
            'title': 'Today in Focus',
            'description': 'md5:9ba5564de5ce897faeb12963f4537a64',
        },
        'playlist_mincount': 35,
    }, {
        'url': 'http://play.acast.com/s/ft-banking-weekly',
        'only_matching': True,
    }]
    _API_BASE_URL = 'https://play.acast.com/api/'
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
                'https://play.acast.com/s/%s/%s' % (channel_slug, cast['url']),
                'ACast', cast['id'])

    def _real_extract(self, url):
        channel_slug = self._match_id(url)
        channel_data = self._download_json(
            self._API_BASE_URL + 'channels/%s' % channel_slug, channel_slug)
        entries = OnDemandPagedList(functools.partial(
            self._fetch_page, channel_slug), self._PAGE_SIZE)
        return self.playlist_result(entries, compat_str(
            channel_data['id']), channel_data['name'], channel_data.get('description'))

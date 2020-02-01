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
        'md5': '16d936099ec5ca2d5869e3a813ee8dc4',
        'info_dict': {
            'id': '2a92b283-1a75-4ad8-8396-499c641de0d9',
            'ext': 'mp3',
            'title': '2. Raggarmordet - Röster ur det förflutna',
            'description': 'md5:4f81f6d8cf2e12ee21a321d8bca32db4',
            'timestamp': 1477346700,
            'upload_date': '20161024',
            'duration': 2766.602563,
            'creator': 'Anton Berg & Martin Johnson',
            'series': 'Spår',
            'episode': '2. Raggarmordet - Röster ur det förflutna',
        }
    }, {
        'url': 'http://embed.acast.com/adambuxton/ep.12-adam-joeschristmaspodcast2015',
        'only_matching': True,
    }, {
        'url': 'https://play.acast.com/s/rattegangspodden/s04e09-styckmordet-i-helenelund-del-22',
        'only_matching': True,
    }, {
        'url': 'https://play.acast.com/s/sparpodcast/2a92b283-1a75-4ad8-8396-499c641de0d9',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel, display_id = re.match(self._VALID_URL, url).groups()
        s = self._download_json(
            'https://feeder.acast.com/api/v1/shows/%s/episodes/%s' % (channel, display_id),
            display_id)
        media_url = s['url']
        if re.search(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}', display_id):
            episode_url = s.get('episodeUrl')
            if episode_url:
                display_id = episode_url
            else:
                channel, display_id = re.match(self._VALID_URL, s['link']).groups()
        cast_data = self._download_json(
            'https://play-api.acast.com/splash/%s/%s' % (channel, display_id),
            display_id)['result']
        e = cast_data['episode']
        title = e.get('name') or s['title']
        return {
            'id': compat_str(e['id']),
            'display_id': display_id,
            'url': media_url,
            'title': title,
            'description': e.get('summary') or clean_html(e.get('description') or s.get('description')),
            'thumbnail': e.get('image'),
            'timestamp': unified_timestamp(e.get('publishingDate') or s.get('publishDate')),
            'duration': float_or_none(e.get('duration') or s.get('duration')),
            'filesize': int_or_none(e.get('contentLength')),
            'creator': try_get(cast_data, lambda x: x['show']['author'], compat_str),
            'series': try_get(cast_data, lambda x: x['show']['name'], compat_str),
            'season_number': int_or_none(e.get('seasonNumber')),
            'episode': title,
            'episode_number': int_or_none(e.get('episodeNumber')),
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

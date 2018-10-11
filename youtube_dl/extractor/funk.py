# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from .nexx import NexxIE
from ..compat import compat_str
from ..utils import (
    int_or_none,
    try_get,
)


class FunkBaseIE(InfoExtractor):
    _HEADERS = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoid2ViYXBwLXYzMSIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxuZXh4LWNvbnRlbnQtYXBpLXYzMSx3ZWJhcHAtYXBpIn0.mbuG9wS9Yf5q6PqgR4fiaRFIagiHk9JhwoKES7ksVX4',
    }
    _AUTH = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoid2ViYXBwLXYzMSIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxuZXh4LWNvbnRlbnQtYXBpLXYzMSx3ZWJhcHAtYXBpIn0.mbuG9wS9Yf5q6PqgR4fiaRFIagiHk9JhwoKES7ksVX4'

    @staticmethod
    def _make_headers(referer):
        headers = FunkBaseIE._HEADERS.copy()
        headers['Referer'] = referer
        return headers

    def _make_url_result(self, video):
        return {
            '_type': 'url_transparent',
            'url': 'nexx:741:%s' % video['sourceId'],
            'ie_key': NexxIE.ie_key(),
            'id': video['sourceId'],
            'title': video.get('title'),
            'description': video.get('description'),
            'duration': int_or_none(video.get('duration')),
            'season_number': int_or_none(video.get('seasonNr')),
            'episode_number': int_or_none(video.get('episodeNr')),
        }


class FunkMixIE(FunkBaseIE):
    _VALID_URL = r'https?://(?:www\.)?funk\.net/mix/(?P<id>[^/]+)/(?P<alias>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.funk.net/mix/59d65d935f8b160001828b5b/die-realste-kifferdoku-aller-zeiten',
        'md5': '8edf617c2f2b7c9847dfda313f199009',
        'info_dict': {
            'id': '123748',
            'ext': 'mp4',
            'title': '"Die realste Kifferdoku aller Zeiten"',
            'description': 'md5:c97160f5bafa8d47ec8e2e461012aa9d',
            'timestamp': 1490274721,
            'upload_date': '20170323',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        mix_id = mobj.group('id')
        alias = mobj.group('alias')

        lists = self._download_json(
            'https://www.funk.net/api/v3.1/curation/curatedLists/',
            mix_id, headers=self._make_headers(url), query={
                'size': 100,
            })['_embedded']['curatedListList']

        metas = next(
            l for l in lists
            if mix_id in (l.get('entityId'), l.get('alias')))['videoMetas']
        video = next(
            meta['videoDataDelegate']
            for meta in metas
            if try_get(
                meta, lambda x: x['videoDataDelegate']['alias'],
                compat_str) == alias)

        return self._make_url_result(video)


class FunkChannelIE(FunkBaseIE):
    _VALID_URL = r'https?://(?:www\.)?funk\.net/channel/(?P<id>[^/]+)/(?P<alias>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.funk.net/channel/ba/die-lustigsten-instrumente-aus-dem-internet-teil-2',
        'info_dict': {
            'id': '1155821',
            'ext': 'mp4',
            'title': 'Die LUSTIGSTEN INSTRUMENTE aus dem Internet - Teil 2',
            'description': 'md5:a691d0413ef4835588c5b03ded670c1f',
            'timestamp': 1514507395,
            'upload_date': '20171229',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # only available via byIdList API
        'url': 'https://www.funk.net/channel/informr/martin-sonneborn-erklaert-die-eu',
        'info_dict': {
            'id': '205067',
            'ext': 'mp4',
            'title': 'Martin Sonneborn erklärt die EU',
            'description': 'md5:050f74626e4ed87edf4626d2024210c0',
            'timestamp': 1494424042,
            'upload_date': '20170510',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.funk.net/channel/59d5149841dca100012511e3/mein-erster-job-lovemilla-folge-1/lovemilla/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        alias = mobj.group('alias')

        headers = self._make_headers(url)

        video = None

        # Id-based channels are currently broken on their side: webplayer
        # tries to process them via byChannelAlias endpoint and fails
        # predictably.
        for page_num in itertools.count():
            by_channel_alias = self._download_json(
                'https://www.funk.net/api/v3.1/webapp/videos/byChannelAlias/%s'
                % channel_id,
                'Downloading byChannelAlias JSON page %d' % (page_num + 1),
                headers=headers, query={
                    'filterFsk': 'false',
                    'sort': 'creationDate,desc',
                    'size': 100,
                    'page': page_num,
                }, fatal=False)
            if not by_channel_alias:
                break
            video_list = try_get(
                by_channel_alias, lambda x: x['_embedded']['videoList'], list)
            if not video_list:
                break
            try:
                video = next(r for r in video_list if r.get('alias') == alias)
                break
            except StopIteration:
                pass
            if not try_get(
                    by_channel_alias, lambda x: x['_links']['next']):
                break

        if not video:
            by_id_list = self._download_json(
                'https://www.funk.net/api/v3.0/content/videos/byIdList',
                channel_id, 'Downloading byIdList JSON', headers=headers,
                query={
                    'ids': alias,
                }, fatal=False)
            if by_id_list:
                video = try_get(by_id_list, lambda x: x['result'][0], dict)

        if not video:
            results = self._download_json(
                'https://www.funk.net/api/v3.0/content/videos/filter',
                channel_id, 'Downloading filter JSON', headers=headers, query={
                    'channelId': channel_id,
                    'size': 100,
                })['result']
            video = next(r for r in results if r.get('alias') == alias)

        return self._make_url_result(video)

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .nexx import NexxIE
from ..utils import int_or_none


class FunkBaseIE(InfoExtractor):
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
            mix_id, headers={
                'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbC12Mi4wIiwic2NvcGUiOiJzdGF0aWMtY29udGVudC1hcGksY3VyYXRpb24tc2VydmljZSxzZWFyY2gtYXBpIn0.SGCC1IXHLtZYoo8PvRKlU2gXH1su8YSu47sB3S4iXBI',
                'Referer': url,
            }, query={
                'size': 100,
            })['result']['lists']

        metas = next(
            l for l in lists
            if mix_id in (l.get('entityId'), l.get('alias')))['videoMetas']
        video = next(
            meta['videoDataDelegate']
            for meta in metas if meta.get('alias') == alias)

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
        'url': 'https://www.funk.net/channel/59d5149841dca100012511e3/mein-erster-job-lovemilla-folge-1/lovemilla/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        alias = mobj.group('alias')

        results = self._download_json(
            'https://www.funk.net/api/v3.0/content/videos/filter', channel_id,
            headers={
                'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbCIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxzZWFyY2gtYXBpIn0.q4Y2xZG8PFHai24-4Pjx2gym9RmJejtmK6lMXP5wAgc',
                'Referer': url,
            }, query={
                'channelId': channel_id,
                'size': 100,
            })['result']

        video = next(r for r in results if r.get('alias') == alias)

        return self._make_url_result(video)

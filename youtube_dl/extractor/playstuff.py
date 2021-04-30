# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError

import json


class PlayStuffIE(InfoExtractor):
    IE_NAME = 'PlayStuff'
    _VALID_URL = r'https://play.stuff.co.nz/details/(?P<id>[0-9a-z_]+)'
    _TESTS = [{
        'url': 'https://play.stuff.co.nz/details/608778ac1de1c4001a3fa09a',
        'md5': 'c82d3669e5247c64bc382577843e5bd0',
        'info_dict': {
            'id': '6250584958001',
            'ext': 'mp4',
            'title': 'Episode 1: Rotorua/Mt Maunganui/Tauranga',
            'description': 'md5:c154bafb9f0dd02d01fd4100fb1c1913',
            'uploader_id': '6005208634001',
            'timestamp': 1619491027,
            'upload_date': '20210427',
        },
        'add_ie': ['BrightcoveNew'],
    }, {
        'url': 'https://play.stuff.co.nz/details/_6089671763001',
        'only_matching': True,
    }]

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/%s_default/index.html?videoId=%s'
    _JSON_RE = r'window.__INITIAL_STATE__ = ({.+});'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info_json = self._search_regex(self._JSON_RE, webpage, 'info')
        entries = []

        if info_json:
            info = json.loads(info_json)

            for itemId, video in info['items'].items():
                if 'content' in video:
                    entries.append({
                        '_type': 'url_transparent',
                        'id': itemId,
                        'url': self.BRIGHTCOVE_URL_TEMPLATE % (
                            info['configurations']['accountId'],
                            info['configurations']['playerId'],
                            video['content']['attributes']['assetId']),
                        'ie_key': 'BrightcoveNew',
                    })

        if not entries:
            raise ExtractorError('No videos found', expected=True)

        return self.playlist_result(
            entries, video_id, self._og_search_title(webpage),
            self._html_search_meta(['og:description', 'description'], webpage))

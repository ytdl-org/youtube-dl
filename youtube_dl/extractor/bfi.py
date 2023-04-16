# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    parse_qs,
    remove_start,
    smuggle_url,
)


class BFIPlayerIE(InfoExtractor):
    IE_NAME = 'bfi:player'
    _VALID_URL = r'https?://player\.bfi\.org\.uk/[^/]+/film/watch-(?P<id>[\w-]+)-online'
    _TEST = {
        'url': 'https://player.bfi.org.uk/free/film/watch-computer-doctor-1974-online',
        'md5': '15598bdd6a413ce9363970754f054d76',
        'info_dict': {
            'id': 'htNnhlZjE60C9VySkQEIBtU-cNV1Xx63',
            'ext': 'mp4',
            'title': 'Computer Doctor',
            'description': 'md5:fb6c240d40c4dbe40428bdd62f78203b',
            'timestamp': 1564424975,
            'upload_date': '20190729',
            'uploader_id': '6057949427001',
        },
        # 'skip': 'BFI Player films cannot be played outside of the UK',
    }
    _BRIGHTCOVE_ACCOUNT_ID = '6057949427001'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        film_only = 'play-film' in parse_qs(url, keep_blank_values=True)

        def entries():
            for player_el in re.finditer(r'(?s)<video-js\b[^>]+>', webpage):
                player_attr = extract_attributes(player_el.group(0))
                bcv_id, account_id, player_id, embed = (
                    player_attr.get(x) for x in ('data-ref-id', 'data-acid', 'data-pid', 'data-embed'))
                if not bcv_id:
                    continue
                if film_only and player_attr.get('data-video-type') != 'film':
                    continue
                bc_url = 'brightcove:new:%s:%s:%s:video:ref:%s' % (
                    account_id or self._BRIGHTCOVE_ACCOUNT_ID, player_id or 'default', embed or 'default', bcv_id)

                yield self.url_result(smuggle_url(
                    bc_url, {'referrer': url, 'force_videoid': remove_start(bcv_id, 'ref:')}), ie='BrightcoveNew', video_id=video_id)

        return self.playlist_result(entries())

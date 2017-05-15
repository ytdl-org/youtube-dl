# coding: utf-8
from __future__ import unicode_literals

import re

from ..compat import compat_etree_fromstring
from ..utils import get_element_by_id, get_element_by_attribute
from .common import InfoExtractor

# TEMP FOR DEV
from pprint import pprint as pp

class PalcoMP3IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?palcomp3\.com/(?P<artist>[^/]+)/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial/nossas-composicoes-cuida-bem-dela/',
        'md5': '99fd6405b2d8fd589670f6db1ba3b358',
        'info_dict': {
            'id': '3162927',
            'ext': 'mp3',
            'display_id': 'nossas-composicoes-cuida-bem-dela',
            'title': 'Nossas Composições - CUIDA BEM DELA',
            'thumbnail': r'https://studiosol-a.akamaihd.net/tb/80x60/palcomp3-logo/9/d/f/c/356447_20170324175145.jpg',
        }},
        {
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial/niveis-da-bebida/',
        'md5': '4c4d1e45b5ae49396cfff017eb41cdd9',
        'info_dict': {
            'id': '2303899',
            'ext': 'mp3',
            'display_id': 'niveis-da-bebida',
            'title': 'NIVEIS DA BEBIDA',
            'thumbnail': r'https://studiosol-a.akamaihd.net/tb/80x60/palcomp3-logo/9/d/f/c/356447_20170324175145.jpg',
        }},
    ]

    def _json_ld(self, json_ld, display_id, fatal=True, expected_type="MusicGroup"):
        """ override `common.py:_json_ld` as we just need the
            `_search_json_ld` function to get the JSON, but the original
            `_json_ld` function does not fit us."""
        return self._parse_json(json_ld, display_id, fatal=fatal)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        print ("Webpage", type(webpage), len(webpage))

        ld = self._get_ld_info(webpage, display_id)
        tracks = [ self._ld_track_process(track, ld) for track in ld['track'] ]
       
        # from IPython import embed
        # embed()
        for track in tracks:
            if track['display_id'] == display_id:
                return track


    def _get_ld_info(self, webpage, display_id):
        # player = get_element_by_attribute('id', 'player', webpage, escape_value=False)
        player = get_element_by_id('player', webpage)
        pp(player)

        ld = self._search_json_ld(player, display_id, expected_type="MusicGroup")
        print("LD:")
        pp(ld)

        return ld

    def _ld_track_process(self, track, ld={'genre':None}):
        tmin, tsec = re.findall("PT(\d+)M(\d+)S", track['duration'], re.IGNORECASE)[0]

        return {
            'id': track['@id'],
            'title': track['name'],
            'track': track['name'],
            'url': 'https:' + track['audio'],
            'webpage_url': 'https://www.palcomp3.com' + track['url'],
            'artist': track['byArtist']['name'],
            'thumbnail': track['byArtist']['image'],
            'display_id': track['url'].split('/')[-2],
            'duration': int(tmin)*60 + int(tsec),
            'genre': ld['genre'],
        }
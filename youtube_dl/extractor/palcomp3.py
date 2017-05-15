# coding: utf-8
from __future__ import unicode_literals

from ..compat import compat_etree_fromstring
from ..utils import get_element_by_id, get_element_by_attribute
from .common import InfoExtractor

# TEMP FOR DEV
from pprint import pprint as pp

class PalcoMP3IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?palcomp3\.com/(?P<artist>[^/]+)/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial/nossas-composicoes-cuida-bem-dela/',
        'md5': '0effca14d6640568df0c1daa1e5609e2',
        'info_dict': {
            'id': 'nossas-composicoes-cuida-bem-dela',
            'ext': 'mp3',
            'title': 'Nossas Composições - CUIDA BEM DELA',
            'thumbnail': r'https://studiosol-a.akamaihd.net/tb/468x351/palcomp3-logo/9/d/f/c/356447_20170324175145.jpg',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _json_ld(self, json_ld, video_id, fatal=True, expected_type="MusicGroup"):
        """ override `common.py:_json_ld` as we just need the
            `_search_json_ld` function to get the JSON, but the original
            `_json_ld` function does not fit us."""
        return self._parse_json(json_ld, video_id, fatal=fatal)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        print ("Webpage", type(webpage), len(webpage))


        player = get_element_by_id('player', webpage)
        # player = get_element_by_attribute('id', 'player', webpage, escape_value=False)
        pp(player)


        
        ld = self._search_json_ld(player, video_id, expected_type="MusicGroup")
        print("LD:")
        pp(ld)

        # from IPython import embed
        # embed()
        info = self._ld_track_process(ld['track'][0])

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            # 'description': self._og_search_description(webpage),
            # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
            'url': 'https:' + ld['track'][0]['audio'],
        }


    def _ld_track_process(self, track):
        return {
            'url': 'https:' + track['audio']
        }
# coding: utf-8
from __future__ import unicode_literals

import re

from ..compat import compat_etree_fromstring
from ..utils import get_element_by_id, get_element_by_attribute
from .common import InfoExtractor

# TEMP FOR DEV
from pprint import pprint as pp

class PalcoMP3IE(InfoExtractor):
    IE_NAME = 'PalcoMP3:song'
    _VALID_URL = r'https?://(?:www\.)?palcomp3\.com/(?P<artist>[^/]+)/(?P<id>[^/]+)/?$'
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
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial/niveis-da-bebida',
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


    def _extract_common(self, url):
        artist_id = self._VALID_URL_RE.match(url).group('artist')
        webpage = self._download_webpage(url, artist_id)
        print ("Webpage", type(webpage), len(webpage))
        self.webpage = webpage

        ld = self._get_ld_info(webpage, artist_id)
        tracks = [ self._ld_track_process(track, ld) for track in ld['track'] ]

        return tracks, ld, webpage

    def _real_extract(self, url, with_webpage=False):
        display_id = self._match_id(url)
        tracks, ld, webpage = self._extract_common(url)
        for track in tracks:
            if track['display_id'] == display_id:
                if with_webpage:
                    return track, webpage
                else:
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


class PalcoMP3ArtistIE(PalcoMP3IE):
    IE_NAME = 'PalcoMP3:artist'
    _VALID_URL = r'https?://(?:www\.)?palcomp3\.com/(?P<artist>[^/]+)/?$'
    _TESTS = [
        {
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial',
        'info_dict': {
            'id': 'maiaraemaraisaoficial',
            'title': 'Maiara e Maraisa Oficial',
            },
        'playlist_count': 8,
        },
        {
        'url': 'https://www.palcomp3.com/banda5cha/',
        'info_dict': {
            'id': 'banda5cha',
            'title': '5Chá',
            },
        'playlist_count': 2,
        },
    ]

    def _real_extract(self, url):
        tracks, ld, _ = self._extract_common(url)
        return self.playlist_result(tracks, ld['name'], ld['description'])


class PalcoMP3VideoIE(PalcoMP3IE):
    IE_NAME = 'PalcoMP3:video'
    _VALID_URL = r'https?://(?:www\.)?palcomp3\.com/(?P<artist>[^/]+)/(?P<id>[^/]+)/#clipe$'
    _TESTS = [
        {
        'url': 'https://www.palcomp3.com/maiaraemaraisaoficial/maiara-e-maraisa-voce-faz-falta-aqui-ao-vivo-em-vicosa-mg/#clipe',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': '_pD1nR2qqPg',
            'ext': 'mp4',
            'title': 'Maiara e Maraisa - Você Faz Falta Aqui - DVD Ao Vivo Em Campo Grande',
            'description': 'md5:739d585d094212b999e507377daa21de',
            'upload_date': '20161107',
            'uploader_id': 'maiaramaraisaoficial',
            'uploader': 'Maiara e Maraisa',
        }},
        {
        'url': 'https://www.palcomp3.com/mckevinho/dog-vagabundo-mc-phe-cachorrera-part-mc-kevinho/#clipe',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': 'iKVAfp6-o-Q',
            'ext': 'mp4',
            'title': 'MC Phe Cachorrera e MC Kevinho - Dog Vagabundo (Video Clipe) Jorgin Deejhay / HDUC ep.2',
            'description': 'md5:728024b6905a9a321c8c16e1e1985e56',
            'upload_date': '20170208',
            'uploader': 'GR6 EXPLODE',
            'uploader_id': 'gr6explode',
        }},
    ]

    def _real_extract(self, url):
        track, webpage = super(PalcoMP3VideoIE, self)._real_extract(url, with_webpage=True)
        print "TRACK"
        pp(track)

        video_re = r"""
            (?x)
            <li (.*?) data-id="{}" (.*?)
                data-id-video="(?P<video_id>[^"]+?)"
            (.*?) >
            <a (.*?) href="([^"]*?)">
            <span>([^<]*?)</span></a></li>
            """.format(track['id'])

        m  = re.search(video_re, webpage)

        # from IPython import embed
        # embed()

        if not m:
            return None

        video_id = m.group('video_id')

        return {
            '_type': 'url_transparent',
            'ie_key': 'Youtube',
            'id': video_id,
            'url': video_id,
        }

# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
)


class IPrimaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:prima|cool|max|zoom|love|play)\.iprima\.cz/(?:.+/)?(?P<id>[^?#]+)'
    _GEO_BYPASS = False

    _TESTS = [{
        'url': 'http://play.iprima.cz/gondici-s-r-o/gondici-s-r-o-34',
        'info_dict': {
            'id': 'p136534',
            'ext': 'mp4',
            'title': 'Gondíci s. r. o. (34)',
            'description': 'md5:16577c629d006aa91f59ca8d8e7f99bd',
        },
        'params': {
            'skip_download': True,  # m3u8 download
        },
    }, {
        'url': 'http://play.iprima.cz/particka/particka-92',
        'only_matching': True,
    }, {
        # geo restricted
        'url': 'http://play.iprima.cz/closer-nove-pripady/closer-nove-pripady/closer-nove-pripady-'
               'iv-1/closer-nove-pripady-iv-1-upoutavka',
        'only_matching': True,
    }, {
        'url': 'http://prima.iprima.cz/zpravodajstvi/10122017-0',
        'info_dict': {
            'id': 'p407787',
            'ext': 'mp4',
            'title': 'Zpravodajství FTV Prima, Zpravodajství FTV Prima 10.12.2017 | Prima',
            'description': 'md5:d3640eaccd3a66423c86f8942d79d5ce',
        },
        'params': {
            'skip_download': True,  # m3u8 download
        },
    }, {
        'url': 'http://cool.iprima.cz/porady/tezka-drina/pila-0',
        'info_dict': {
            'id': 'p32629',
            'ext': 'mp4',
            'title': 'Těžká dřina, 5. epizoda - Pila | Prima Cool',
            'description': 'md5:ab9ad7b8af739fed79185c4e58bc599d',
        },
        'params': {
            'skip_download': True,  # m3u8 download
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(r'(?:prehravac/embedded\?id=|productId: \')(p[0-9]+)', webpage, 'real id')

        playerpage = self._download_webpage(
            'http://api.play-backend.iprima.cz/prehravac/init-embed',
            video_id, note='Downloading player', query={
                '_infuse': 1,
                '_ts': round(time.time()),
                'productId': video_id,
                'embed': 'true',
            }, headers={'Referer': 'http://api.play-backend.iprima.cz/prehravac/embedded?id=' + video_id})

        formats = []

        def extract_formats(format_url, format_key=None, lang=None):
            ext = determine_ext(format_url)
            new_formats = []
            if format_key == 'hls' or ext == 'm3u8':
                new_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False)
            elif format_key == 'dash' or ext == 'mpd':
                return
                new_formats = self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False)
            if lang:
                for f in new_formats:
                    if not f.get('language'):
                        f['language'] = lang
            formats.extend(new_formats)

        options = self._parse_json(
            self._search_regex(
                r'(?s)(?:TDIPlayerOptions|playerOptions)\s*=\s*({.+?});\s*\]\]',
                playerpage, 'player options', default='{}'),
            video_id, transform_source=js_to_json, fatal=False)
        if options:
            for key, tracks in options.get('tracks', {}).items():
                if not isinstance(tracks, list):
                    continue
                for track in tracks:
                    src = track.get('src')
                    if src:
                        extract_formats(src, key.lower(), track.get('lang'))

        if not formats:
            for _, src in re.findall(r'src["\']\s*:\s*(["\'])(.+?)\1', playerpage):
                extract_formats(src)

        if not formats and '>GEO_IP_NOT_ALLOWED<' in playerpage:
            self.raise_geo_restricted(countries=['CZ'])

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }

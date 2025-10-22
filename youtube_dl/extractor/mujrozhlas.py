# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
    js_to_json,
)


class MujRozhlasIE(InfoExtractor):
    IE_NAME = 'mujRozhlas'
    IE_DESC = 'https://www.mujrozhlas.cz/'
    _VALID_URL = r'https?://www\.mujrozhlas\.cz/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [
        {
            'url': 'https://www.mujrozhlas.cz/vinohradska-12/zadne-dalsi-pusy-konec-prchala-spol-muze-znamenat-babisuv-odchod-z-politiky-tipuje',
            'md5': '34ecaa47f64079a63d6b80498c280e9d',
            'info_dict': {
                'id': '0c54ba72-93dd-3a29-b567-910d3d8c71a8',
                'ext': 'mp3',
                'title': 'Žádné další pusy. Konec Prchala a spol. může znamenat Babišův odchod z politiky, tipuje politolog',
                'description': 'md5:ec0610bdb1f591061dbd224d2dd9c19e',
            },
        },
        {
            'url': 'https://www.mujrozhlas.cz/kazki/princi-ta-zliy-drakon',
            'md5': 'cbad6f68db6dc4d6d798d69b5d258aa5',
            'info_dict': {
                'id': 'ec5f53b2-3910-448e-8e7f-d6d1a19f4926',
                'ext': 'm4a',
                'title': 'Принці та злий дракон',
                'description': 'md5:b21701e09c2b509c4451194af7ac271b',
            },
            'params': {
                'format': 'hls-128',
            },
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        player_data = self._search_regex(
            r'\bvar dl = ({[^\n]+});',
            webpage, 'player data', default=None)
        if not player_data:
            raise ExtractorError('Could not find player data')

        player_data = self._parse_json(player_data, display_id, js_to_json)
        audio_id = player_data['contentId']
        bundle = player_data['siteEntityBundle']
        if bundle not in ('episode', 'serialPart'):
            raise ExtractorError('Unsupported entity: {0}'.format(bundle))

        url = 'https://api.mujrozhlas.cz/episodes/{0}'.format(player_data['contentId'])
        webpage = self._download_webpage(url, audio_id)
        attr = self._parse_json(webpage, audio_id)['data']['attributes']

        formats = []
        for link in attr['audioLinks']:
            variant = link['variant']
            if variant == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    link['url'], audio_id, 'm4a', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif variant == 'dash':
                formats.extend(self._extract_mpd_formats(
                    link['url'], audio_id, mpd_id='dash', fatal=False))
            elif variant == 'mp3':
                url = link['url']
                m = re.search(
                    r'(?P<proto>[^:]+):(?:.*/)*(?P<id>[^.]+)\.(?P<ext>[^/.]+)$',
                    url)
                bitrate = link['bitrate']
                formats.append({
                    'url': link['url'],
                    'protocol': m.group('proto'),
                    'ext': m.group('ext'),
                    'format_id': '-'.join(('mp3', str(bitrate))),
                    'vcodec': 'none',
                    'abr': bitrate,
                    'tbr': bitrate,
                })
        self._sort_formats(formats)

        return {
            'id': audio_id,
            'title': attr['title'],
            'description': clean_html(attr['description']),
            'formats': formats,
        }

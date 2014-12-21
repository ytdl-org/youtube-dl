# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    unescapeHTML,
    ExtractorError,
)


class DVTVIE(InfoExtractor):
    IE_NAME = 'dvtv'
    IE_DESC = 'http://video.aktualne.cz/'

    _VALID_URL = r'http://video\.aktualne\.cz/(?:[^/]+/)+r~(?P<id>[0-9a-f]{32})'

    _TESTS = [{
        'url': 'http://video.aktualne.cz/dvtv/vondra-o-ceskem-stoleti-pri-pohledu-na-havla-mi-bylo-trapne/r~e5efe9ca855511e4833a0025900fea04/',
        'md5': '67cb83e4a955d36e1b5d31993134a0c2',
        'info_dict': {
            'id': 'dc0768de855511e49e4b0025900fea04',
            'ext': 'mp4',
            'title': 'Vondra o Českém století: Při pohledu na Havla mi bylo trapně',
        }
    }, {
        'url': 'http://video.aktualne.cz/dvtv/stropnicky-policie-vrbetice-preventivne-nekontrolovala/r~82ed4322849211e4a10c0025900fea04/',
        'md5': '6388f1941b48537dbd28791f712af8bf',
        'info_dict': {
            'id': '72c02230849211e49f60002590604f2e',
            'ext': 'mp4',
            'title': 'Stropnický: Policie Vrbětice preventivně nekontrolovala',
        }
    }, {
        'url': 'http://video.aktualne.cz/dvtv/dvtv-16-12-2014-utok-talibanu-boj-o-kliniku-uprchlici/r~973eb3bc854e11e498be002590604f2e/',
        'info_dict': {
            'title': 'DVTV 16. 12. 2014: útok Talibanu, boj o kliniku, uprchlíci',
            'id': '973eb3bc854e11e498be002590604f2e',
        },
        'playlist': [{
            'md5': 'da7ca6be4935532241fa9520b3ad91e4',
            'info_dict': {
                'id': 'b0b40906854d11e4bdad0025900fea04',
                'ext': 'mp4',
                'title': 'Drtinová Veselovský TV 16. 12. 2014: Témata dne'
            }
        }, {
            'md5': '5f7652a08b05009c1292317b449ffea2',
            'info_dict': {
                'id': '420ad9ec854a11e4bdad0025900fea04',
                'ext': 'mp4',
                'title': 'Školní masakr možná změní boj s Talibanem, říká novinářka'
            }
        }, {
            'md5': '498eb9dfa97169f409126c617e2a3d64',
            'info_dict': {
                'id': '95d35580846a11e4b6d20025900fea04',
                'ext': 'mp4',
                'title': 'Boj o kliniku: Veřejný zájem, nebo právo na majetek?'
            }
        }, {
            'md5': 'b8dc6b744844032dab6ba3781a7274b9',
            'info_dict': {
                'id': '6fe14d66853511e4833a0025900fea04',
                'ext': 'mp4',
                'title': 'Pánek: Odmítání syrských uprchlíků je ostudou české vlády'
            }
        }],
    }, {
        'url': 'http://video.aktualne.cz/v-cechach-poprve-zazni-zelenkova-zrestaurovana-mse/r~45b4b00483ec11e4883b002590604f2e/',
        'only_matching': True,
    }]

    def _parse_video_metadata(self, js, video_id):
        metadata = self._parse_json(js, video_id, transform_source=js_to_json)

        formats = []
        for video in metadata['sources']:
            ext = video['type'][6:]
            formats.append({
                'url': video['file'],
                'ext': ext,
                'format_id': '%s-%s' % (ext, video['label']),
                'height': int(video['label'].rstrip('p')),
                'fps': 25,
            })

        self._sort_formats(formats)

        return {
            'id': metadata['mediaid'],
            'title': unescapeHTML(metadata['title']),
            'thumbnail': self._proto_relative_url(metadata['image'], 'http:'),
            'formats': formats
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # single video
        item = self._search_regex(
            r"(?s)embedData[0-9a-f]{32}\['asset'\]\s*=\s*(\{.+?\});",
            webpage, 'video', default=None, fatal=False)

        if item:
            return self._parse_video_metadata(item, video_id)

        # playlist
        items = re.findall(
            r"(?s)BBX\.context\.assets\['[0-9a-f]{32}'\]\.push\(({.+?})\);",
            webpage)

        if items:
            return {
                '_type': 'playlist',
                'id': video_id,
                'title': self._og_search_title(webpage),
                'entries': [self._parse_video_metadata(i, video_id) for i in items]
            }

        raise ExtractorError('Could not find neither video nor playlist')

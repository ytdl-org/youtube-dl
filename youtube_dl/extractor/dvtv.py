# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    js_to_json,
    mimetype2ext,
    unescapeHTML,
)


class DVTVIE(InfoExtractor):
    IE_NAME = 'dvtv'
    IE_DESC = 'http://video.aktualne.cz/'

    _VALID_URL = r'https?://video\.aktualne\.cz/(?:[^/]+/)+r~(?P<id>[0-9a-f]{32})'

    _TESTS = [{
        'url': 'http://video.aktualne.cz/dvtv/vondra-o-ceskem-stoleti-pri-pohledu-na-havla-mi-bylo-trapne/r~e5efe9ca855511e4833a0025900fea04/',
        'md5': '67cb83e4a955d36e1b5d31993134a0c2',
        'info_dict': {
            'id': 'dc0768de855511e49e4b0025900fea04',
            'ext': 'mp4',
            'title': 'Vondra o Českém století: Při pohledu na Havla mi bylo trapně',
            'duration': 1484,
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
                'title': 'Drtinová Veselovský TV 16. 12. 2014: Témata dne',
                'description': 'md5:0916925dea8e30fe84222582280b47a0',
                'timestamp': 1418760010,
                'upload_date': '20141216',
            }
        }, {
            'md5': '5f7652a08b05009c1292317b449ffea2',
            'info_dict': {
                'id': '420ad9ec854a11e4bdad0025900fea04',
                'ext': 'mp4',
                'title': 'Školní masakr možná změní boj s Talibanem, říká novinářka',
                'description': 'md5:ff2f9f6de73c73d7cef4f756c1c1af42',
                'timestamp': 1418760010,
                'upload_date': '20141216',
            }
        }, {
            'md5': '498eb9dfa97169f409126c617e2a3d64',
            'info_dict': {
                'id': '95d35580846a11e4b6d20025900fea04',
                'ext': 'mp4',
                'title': 'Boj o kliniku: Veřejný zájem, nebo právo na majetek?',
                'description': 'md5:889fe610a70fee5511dc3326a089188e',
                'timestamp': 1418760010,
                'upload_date': '20141216',
            }
        }, {
            'md5': 'b8dc6b744844032dab6ba3781a7274b9',
            'info_dict': {
                'id': '6fe14d66853511e4833a0025900fea04',
                'ext': 'mp4',
                'title': 'Pánek: Odmítání syrských uprchlíků je ostudou české vlády',
                'description': 'md5:544f86de6d20c4815bea11bf2ac3004f',
                'timestamp': 1418760010,
                'upload_date': '20141216',
            }
        }],
    }, {
        'url': 'https://video.aktualne.cz/dvtv/zeman-si-jen-leci-mindraky-sobotku-nenavidi-a-babis-se-mu-te/r~960cdb3a365a11e7a83b0025900fea04/',
        'md5': 'f8efe9656017da948369aa099788c8ea',
        'info_dict': {
            'id': '3c496fec365911e7a6500025900fea04',
            'ext': 'mp4',
            'title': 'Zeman si jen léčí mindráky, Sobotku nenávidí a Babiš se mu teď hodí, tvrdí Kmenta',
            'duration': 1103,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://video.aktualne.cz/v-cechach-poprve-zazni-zelenkova-zrestaurovana-mse/r~45b4b00483ec11e4883b002590604f2e/',
        'only_matching': True,
    }]

    def _parse_video_metadata(self, js, video_id):
        data = self._parse_json(js, video_id, transform_source=js_to_json)

        title = unescapeHTML(data['title'])

        formats = []
        for video in data['sources']:
            video_url = video.get('file')
            if not video_url:
                continue
            video_type = video.get('type')
            ext = determine_ext(video_url, mimetype2ext(video_type))
            if video_type == 'application/vnd.apple.mpegurl' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif video_type == 'application/dash+xml' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, mpd_id='dash', fatal=False))
            else:
                label = video.get('label')
                height = self._search_regex(
                    r'^(\d+)[pP]', label or '', 'height', default=None)
                format_id = ['http']
                for f in (ext, label):
                    if f:
                        format_id.append(f)
                formats.append({
                    'url': video_url,
                    'format_id': '-'.join(format_id),
                    'height': int_or_none(height),
                })
        self._sort_formats(formats)

        return {
            'id': data.get('mediaid') or video_id,
            'title': title,
            'description': data.get('description'),
            'thumbnail': data.get('image'),
            'duration': int_or_none(data.get('duration')),
            'timestamp': int_or_none(data.get('pubtime')),
            'formats': formats
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # single video
        item = self._search_regex(
            r'(?s)embedData[0-9a-f]{32}\[["\']asset["\']\]\s*=\s*(\{.+?\});',
            webpage, 'video', default=None, fatal=False)

        if item:
            return self._parse_video_metadata(item, video_id)

        # playlist
        items = re.findall(
            r"(?s)BBX\.context\.assets\['[0-9a-f]{32}'\]\.push\(({.+?})\);",
            webpage)
        if not items:
            items = re.findall(r'(?s)var\s+asset\s*=\s*({.+?});\n', webpage)

        if items:
            return {
                '_type': 'playlist',
                'id': video_id,
                'title': self._og_search_title(webpage),
                'entries': [self._parse_video_metadata(i, video_id) for i in items]
            }

        raise ExtractorError('Could not find neither video nor playlist')

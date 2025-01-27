# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    extract_attributes,
    merge_dicts,
    mimetype2ext,
    parse_duration,
    parse_qs,
    T,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class RTVSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:rtvs|stvr)\.sk/(?:radio|televizia)/archiv(?:/\d+)?/(?P<id>\d+)'
    _TESTS = [{
        # radio archive
        'url': 'http://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '414872',
            'display_id': '135331',
            'ext': 'mp3',
            'title': 'Ostrov pokladov 1 časť.mp3',
            'duration': 2854,
            'thumbnail': (
                r're:https?://www\.(?:(?P<stvr>stvr)|rtvs)\.sk'
                '/media/a501/image/file/2/0000'
                r'/(?(stvr)rtvs-00009383\.png|b1R8\.rtvs\.jpg)$'
            ),
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # tv archive
        'url': 'http://www.rtvs.sk/televizia/archiv/8249/63118',
        'md5': '85e2c55cf988403b70cac24f5c086dc6',
        'info_dict': {
            'id': '63118',
            'ext': 'mp4',
            'title': 'Amaro Džives - Náš deň',
            'description': r're:Cenu Romipen odovzdá .{292} Medzinárodný deň Rómov a prezentovať rómsku kultúru\.$',
            'timestamp': 1428523500,
            'upload_date': '20150408',
            'thumbnail': (
                r're:https://www\.(?:stvr|rtvs)\.sk'
                '/media/a501/image/file/2/0031'
                r'/L7Qm\.amaro_dzives_png\.jpg$'),
            'duration': 4986,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # tv archive
        'url': 'https://www.rtvs.sk/televizia/archiv/18083?utm_source=web&utm_medium=rozcestnik&utm_campaign=Robin',
        'info_dict': {
            'id': '18083',
            'display_id': '457086',
            'ext': 'mp4',
            'title': 'Robin - Vodiace psy /2.časť/',
            'description': r're:Richard so svojím psom Robinom .{49} úlohu vodiace psíky\.$',
            'timestamp': 1711875000,
            'upload_date': '20240331',
            'duration': 931,
            'thumbnail': r're:https://www\.(:rtvs|stvr)\.sk/media/a501/image/file/2/0916/robin\.jpg$',
        }
    }, {
        # new domain
        'url': 'https://www.stvr.sk/televizia/archiv/15135/512191',
        'info_dict': {
            'id': '512191',
            'ext': 'mp4',
            'title': 'Retro noviny',
            'description': r're:Kolekciu spravodajských šotov .{62} uvádza Milan Antonič, archivár STV\.',
            'timestamp': 1737797700,
            'upload_date': '20250125',
            'duration': 1686,
            'thumbnail': 'https://www.stvr.sk/media/a501/image/file/2/0519/NSF4.retro_noviny_jpg.jpg',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        iframe_url = info and self._search_regex(
            r'"embedUrl"\s*:\s*"(https?://[^"]+)"', webpage, 'Iframe URL', default=None)
        if not iframe_url:
            iframe = self._search_regex(
                r'''(<iframe\s[^>]*(?<!-)\bid\s*=\s*['"]?player_(?:(?!_)\w)+_\d+[^>]+>)''',
                webpage, 'Iframe')
            iframe = extract_attributes(iframe)

            iframe_url = iframe['src']

        webpage = self._download_webpage(iframe_url, video_id, 'Downloading iframe')
        json_url = self._search_regex(r'var\s+url\s*=\s*"([^"]+)"\s*\+\s*ruurl', webpage, 'json URL')
        data = self._download_json('https:{0}b=mozilla&p=win&v=97&f=0&d=1'.format(json_url), video_id)

        if traverse_obj(data, 'clip', expected_type=dict):
            data['playlist'] = [data['clip']]

        formats = []
        _require = lambda k: (lambda x: x if x.get(k) else None)
        for item in traverse_obj(data, (
                'playlist', 0, 'sources', Ellipsis, {
                    'src': ('src', T(url_or_none)),
                    'type': 'type',
                }, T(_require('src')))):
            item_type = item.get('type')
            if item_type == 'application/x-mpegurl':
                formats.extend(self._extract_m3u8_formats(
                    item['src'], video_id, ext='mp4',
                    entry_protocol='m3u8_native', fatal=False))
            elif item_type == 'application/dash+xml':
                formats.extend(self._extract_mpd_formats(
                    item['src'], video_id, fatal=False))
            else:
                formats.append({
                    'url': item['src'],
                    'ext': mimetype2ext(item_type),
                })
        self._sort_formats(formats)

        return merge_dicts({
            'id': video_id,
            'display_id': traverse_obj(parse_qs(json_url), ('id', -1)),
            'formats': formats,
        }, info or traverse_obj(data, ('playlist', 0, {
            'title': 'title',
            'description': ('description', T(lambda s: s.strip())),
            'duration': ('length', T(parse_duration)),
            'thumbnail': ('image', T(url_or_none)),
            'timestamp': ('datetime_create', T(unified_timestamp)),
        })))

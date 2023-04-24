# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    merge_dicts,
    parse_codecs,
    urljoin,
)


class StreamCZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:stream|televizeseznam)\.cz/[^?#]+/(?P<display_id>[^?#]+)-(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.televizeseznam.cz/video/lajna/buh-57953890',
        'md5': '40c41ade1464a390a0b447e333df4239',
        'info_dict': {
            'id': '57953890',
            'ext': 'mp4',
            'title': 'Bůh',
            'display_id': 'buh',
            'description': 'md5:8f5f09b9b7bc67df910486cdd88f7165',
            'duration': 1369.6,
            'view_count': int,
        }
    }, {
        'url': 'https://www.stream.cz/kdo-to-mluvi/kdo-to-mluvi-velke-odhaleni-prinasi-novy-porad-uz-od-25-srpna-64087937',
        'md5': '41fd358000086a1ccdb068c77809b158',
        'info_dict': {
            'id': '64087937',
            'ext': 'mp4',
            'title': 'Kdo to mluví? Velké odhalení přináší nový pořad už od 25. srpna',
            'display_id': 'kdo-to-mluvi-velke-odhaleni-prinasi-novy-porad-uz-od-25-srpna',
            'description': 'md5:97a811000a6460266029d6c1c2ebcd59',
            'duration': 50.2,
            'view_count': int,
        }
    }, {
        'url': 'https://www.stream.cz/tajemno/znicehonic-jim-skrz-strechu-prolitnul-zahadny-predmet-badatele-vse-objasnili-64147267',
        'md5': '3ee4d0be040e8f4a543e67e509d55e3f',
        'info_dict': {
            'id': '64147267',
            'ext': 'mp4',
            'title': 'Zničehonic jim skrz střechu prolítnul záhadný předmět. Badatelé vše objasnili',
            'display_id': 'znicehonic-jim-skrz-strechu-prolitnul-zahadny-predmet-badatele-vse-objasnili',
            'description': 'md5:4b8ada6718d34bb011c4e04ca4bc19bf',
            'duration': 442.84,
            'view_count': int,
        }
    }]

    def _extract_formats(self, spl_url, video):
        for ext, pref, streams in (
                ('ts', -1, video.get('http_stream', {}).get('qualities', {})),
                ('mp4', 1, video.get('mp4'))):
            for format_id, stream in streams.items():
                if not stream.get('url'):
                    continue
                yield merge_dicts({
                    'format_id': '-'.join((format_id, ext)),
                    'ext': ext,
                    'source_preference': pref,
                    'url': urljoin(spl_url, stream['url']),
                    'tbr': float_or_none(stream.get('bandwidth'), scale=1000),
                    'duration': float_or_none(stream.get('duration'), scale=1000),
                    'width': stream.get('resolution', 2 * [0])[0] or None,
                    'height': stream.get('resolution', 2 * [0])[1] or int_or_none(format_id.replace('p', '')),
                }, parse_codecs(stream.get('codec')))

    def _real_extract(self, url):
        display_id, video_id = re.match(self._VALID_URL, url).groups()

        data = self._download_json(
            'https://www.televizeseznam.cz/api/graphql', video_id, 'Downloading GraphQL result',
            data=json.dumps({
                'variables': {'urlName': video_id},
                'query': '''
                    query LoadEpisode($urlName : String){ episode(urlName: $urlName){ ...VideoDetailFragmentOnEpisode } }
                    fragment VideoDetailFragmentOnEpisode on Episode {
                        id
                        spl
                        urlName
                        name
                        perex
                        duration
                        views
                    }'''
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json;charset=UTF-8'}
        )['data']['episode']

        spl_url = data['spl'] + 'spl2,3'
        metadata = self._download_json(spl_url, video_id, 'Downloading playlist')
        if 'Location' in metadata and 'data' not in metadata:
            spl_url = metadata['Location']
            metadata = self._download_json(spl_url, video_id, 'Downloading redirected playlist')
        video = metadata['data']

        subtitles = {}
        for subs in video.get('subtitles', {}).values():
            if not subs.get('language'):
                continue
            for ext, sub_url in subs.get('urls').items():
                subtitles.setdefault(subs['language'], []).append({
                    'ext': ext,
                    'url': urljoin(spl_url, sub_url)
                })

        formats = list(self._extract_formats(spl_url, video))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': data.get('name'),
            'description': data.get('perex'),
            'duration': float_or_none(data.get('duration')),
            'view_count': int_or_none(data.get('views')),
            'formats': formats,
            'subtitles': subtitles,
        }

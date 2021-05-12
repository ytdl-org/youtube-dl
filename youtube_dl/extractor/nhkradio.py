# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_iso8601


class NhkRadioBase(InfoExtractor):
    _GEO_COUNTRIES = ['JP']

    def _get_json_meta(self, program_id, corner_id):
        data = self._download_json(
            'https://www.nhk.or.jp/radioondemand/json/%s/bangumi_%s_%s.json' % (
                program_id, program_id, corner_id),
            program_id + '_' + corner_id)

        return data.get('main')

    def _extract_program(self, data, file_id=None):
        entries = []

        for headline in data.get('detail_list'):
            for entry in headline.get('file_list'):
                entry_id = entry.get('file_id')

                if file_id and file_id != entry_id:
                    continue

                formats = self._extract_m3u8_formats(
                    entry.get('file_name'), entry_id, 'm4a',
                    entry_protocol='m3u8_native', m3u8_id='hls')

                self._sort_formats(formats)

                entries.append({
                    'id': entry_id,
                    'title': entry.get('file_title'),
                    'alt_title': entry.get('file_title_sub'),
                    'series': data.get('program_name'),
                    'season': headline.get('headline'),
                    'season_id': headline.get('headline_id'),
                    'episode_number': entry.get('seq'),
                    'formats': formats,
                    'timestamp': parse_iso8601(entry.get('open_time')),
                })

        return entries


class NhkRadioIE(NhkRadioBase):
    _VALID_URL = r'https?://www\.nhk\.or\.jp/radio/player/ondemand\.html\?p=(?P<program_id>[^/?#&_]+)_(?P<corner_id>[^/?#&_]+)_(?P<file_id>[^/?#&_]+)'

    _TESTS = [
        {
            'url': 'https://www.nhk.or.jp/radio/player/ondemand.html?p=0962_01_42354',
            'info_dict': {
                'id': '42354',
                'ext': 'm4a',
                'title': '(1) 電話のかけ方のポイント',
                'series': 'ことば力アップ',
                'season': '就活に役立つ　実践「敬語」(3)「シーン別、電話コミュニケーション」',
                'season_id': '09',
                'episode_number': 1,
                'upload_date': '20201119',
                'timestamp': int,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.nhk.or.jp/radio/player/ondemand.html?p=P006500_06_44092',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        program_id, corner_id, file_id = re.match(self._VALID_URL, url).groups()
        data = self._get_json_meta(program_id, corner_id)

        for entry in self._extract_program(data, file_id):
            return entry


class NhkRadioProgramIE(NhkRadioBase):
    _VALID_URL = r'https?://www\.nhk\.or\.jp/radio/ondemand/detail\.html\?p=(?P<path>(?P<program_id>[^/?#&_]+)_(?P<corner_id>[^/?#&_]+))'

    _TESTS = [
        {
            'url': 'https://www.nhk.or.jp/radio/ondemand/detail.html?p=0164_01',
            'info_dict': {
                'title': '青春アドベンチャー',
                'id': '0164_01',
            },
            'playlist_mincount': 5,
        },
        {
            'url': 'https://www.nhk.or.jp/radio/ondemand/detail.html?p=P006500_06',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        path, program_id, corner_id = re.match(self._VALID_URL, url).groups()
        data = self._get_json_meta(program_id, corner_id)

        return self.playlist_result(
            self._extract_program(data), path, data.get('program_name'))

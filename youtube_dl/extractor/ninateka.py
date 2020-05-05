# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
)


class NinatekaIE(InfoExtractor):
    IE_NAME = 'ninateka'
    IE_DESC = 'Ninateka'
    _VALID_URL = r'https?://ninateka\.pl/film/(?P<id>[^/\?#]+)'
    _TEST = {
        'url': 'https://ninateka.pl/film/dziwne-przygody-kota-filemona-7',
        'md5': 'f39eebfad3a609df9c90a45a3155393d',
        'info_dict': {
            'id': 'dziwne-przygody-kota-filemona-7',
            'ext': 'mp4',
            'title': 'Dziwny świat kota Filemona | Poważne zmartwienie',
            'description': 'Filemon ma kłopot z własnym wyglądem, czy uda mu się z nim uporać?',
        }
    }

    def decode_url(self, encoded):
        xor_val = ord('h') ^ ord(encoded[0])
        return ''.join(chr(ord(c) ^ xor_val) for c in encoded)

    def extract_formats(self, data, video_id, name):
        info = self._parse_json(data, video_id, transform_source=js_to_json)
        formats = []

        for source_info in info['sources']:
            url = self.decode_url(source_info['src'])
            type_ = source_info.get('type')

            if type_ == 'application/vnd.ms-sstr+xml' or url.endswith('/Manifest'):
                formats.extend(self._extract_ism_formats(
                    url, video_id, ism_id='mss-{}'.format(name), fatal=False))

            elif type_ == 'application/x-mpegURL' or url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    url, video_id, ext='mp4', m3u8_id='hls-{}'.format(name), fatal=False))

            elif type_ == 'application/dash+xml' or url.endswith('.mpd'):
                formats.extend(self._extract_mpd_formats(
                    url, video_id, mpd_id='dash-{}'.format(name), fatal=False))

            elif url.endswith('.f4m'):
                formats.extend(self._extract_f4m_formats(
                    url, video_id, f4m_id='hds-{}'.format(name), fatal=False))

            else:
                formats.append({
                    'format_id': 'direct-{}'.format(name),
                    'url': url,
                    'ext': determine_ext(url, 'mp4'),
                })

        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        main = self._search_regex(
            r'(?m)(?:var|let|const)\s+playerOptionsWithMainSource\s*=\s*(\{.*?\})\s*;\s*?$',
            webpage, 'main source')
        formats = self.extract_formats(main, video_id, 'main')

        audiodesc = self._search_regex(
            r'(?m)(?:var|let|const)\s+playerOptionsWithAudioDescriptionSource\s*=\s*(\{.*?\})\s*;\s*?$',
            webpage, 'audio description', default=None)
        if audiodesc:
            formats.extend(self.extract_formats(audiodesc, video_id, 'audiodescription'))

        english_ver = self._search_regex(
            r'(?m)(?:var|let|const)\s+playerOptionsWithEnglishVersion\s*=\s*(\{.*?\})\s*;\s*?$',
            webpage, 'english version', default=None)
        if english_ver:
            formats.extend(self.extract_formats(english_ver, video_id, 'english'))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    decode_packed_codes,
    ExtractorError,
    parse_duration
)


class CDAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|ebd)\.)?cda\.pl/(?:video|[0-9]+x[0-9]+)/(?P<id>[0-9a-z]+)'
    _TESTS = [
        {
            'url': 'http://www.cda.pl/video/5749950c',
            'md5': '6f844bf51b15f31fae165365707ae970',
            'info_dict': {
                'id': '5749950c',
                'ext': 'mp4',
                'height': 720,
                'title': 'Oto dlaczego przed zakrętem należy zwolnić.',
                'duration': 39
            }
        },
        {
            'url': 'http://www.cda.pl/video/57413289',
            'md5': 'a88828770a8310fc00be6c95faf7f4d5',
            'info_dict': {
                'id': '57413289',
                'ext': 'mp4',
                'title': 'Lądowanie na lotnisku na Maderze',
                'duration': 137
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://ebd.cda.pl/0x0/' + video_id, video_id)

        if 'Ten film jest dostępny dla użytkowników premium' in webpage:
            raise ExtractorError('This video is only available for premium users.', expected=True)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title', fatal=False)

        def _get_format(page, version=''):
            unpacked = decode_packed_codes(page)
            duration = self._search_regex(r"duration:\\'(.+?)\\'", unpacked, 'duration', fatal=False)
            format_id = None
            height = None

            m = re.search(r'<a data-quality="(?P<format_id>[^"]+)" href="[^"]+" class="quality-btn quality-btn-active">(?P<height>[0-9]+)p<\/a>', page)
            if m:
                format_id = m.group('format_id')
                height = int(m.group('height'))

            url = self._search_regex(r"url:\\'(.+?)\\'", unpacked, version + ' url', fatal=False)
            if url is None:
                return None

            return {
                'format_id': format_id,
                'height': height,
                'url': url
            }, parse_duration(duration)

        formats = []

        format_desc, duration = _get_format(webpage) or (None, None)
        if format_desc is not None:
            formats.append(format_desc)

        pattern = re.compile(r'<a data-quality="[^"]+" href="([^"]+)" class="quality-btn">([0-9]+p)<\/a>')
        for version in re.findall(pattern, webpage):
            webpage = self._download_webpage(version[0], video_id, 'Downloading %s version information' % version[1], fatal=False)
            if not webpage:
                # Manually report warning because empty page is returned when invalid version is requested.
                self.report_warning('Unable to download %s version information' % version[1])
                continue

            format_desc, duration_ = _get_format(webpage, version[1]) or (None, None)
            duration = duration or duration_
            if format_desc is not None:
                formats.append(format_desc)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration
        }

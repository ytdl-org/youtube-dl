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
    _VALID_URL = r'https?://(?:(?:www\.)?cda\.pl/video|ebd\.cda\.pl/[0-9]+x[0-9]+)/(?P<id>[0-9a-z]+)'
    _TESTS = [{
        'url': 'http://www.cda.pl/video/5749950c',
        'md5': '6f844bf51b15f31fae165365707ae970',
        'info_dict': {
            'id': '5749950c',
            'ext': 'mp4',
            'height': 720,
            'title': 'Oto dlaczego przed zakrętem należy zwolnić.',
            'duration': 39
        }
    }, {
        'url': 'http://www.cda.pl/video/57413289',
        'md5': 'a88828770a8310fc00be6c95faf7f4d5',
        'info_dict': {
            'id': '57413289',
            'ext': 'mp4',
            'title': 'Lądowanie na lotnisku na Maderze',
            'duration': 137
        }
    }, {
        'url': 'http://ebd.cda.pl/0x0/5749950c',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://ebd.cda.pl/0x0/' + video_id, video_id)

        if 'Ten film jest dostępny dla użytkowników premium' in webpage:
            raise ExtractorError('This video is only available for premium users.', expected=True)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        formats = []

        info_dict = {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': None,
        }

        def extract_format(page, version):
            unpacked = decode_packed_codes(page)
            format_url = self._search_regex(
                r"url:\\'(.+?)\\'", unpacked, '%s url' % version, fatal=False)
            if not format_url:
                return
            f = {
                'url': format_url,
            }
            m = re.search(
                r'<a[^>]+data-quality="(?P<format_id>[^"]+)"[^>]+href="[^"]+"[^>]+class="[^"]*quality-btn-active[^"]*">(?P<height>[0-9]+)p',
                page)
            if m:
                f.update({
                    'format_id': m.group('format_id'),
                    'height': int(m.group('height')),
                })
            info_dict['formats'].append(f)
            if not info_dict['duration']:
                info_dict['duration'] = parse_duration(self._search_regex(
                    r"duration:\\'(.+?)\\'", unpacked, 'duration', fatal=False))

        extract_format(webpage, 'default')

        for href, resolution in re.findall(
                r'<a[^>]+data-quality="[^"]+"[^>]+href="([^"]+)"[^>]+class="quality-btn"[^>]*>([0-9]+p)',
                webpage):
            webpage = self._download_webpage(
                href, video_id, 'Downloading %s version information' % resolution, fatal=False)
            if not webpage:
                # Manually report warning because empty page is returned when
                # invalid version is requested.
                self.report_warning('Unable to download %s version information' % resolution)
                continue
            extract_format(webpage, resolution)

        self._sort_formats(formats)

        return info_dict

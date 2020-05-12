# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import clean_html, ExtractorError


class Doramasmp4IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www8\.)?doramasmp4\.com/(?P<id>[^/]+)'
    _TESTS = [
        {
            'url': 'https://www8.doramasmp4.com/the-man-inside-me/',
            'info_dict': {
                'id': 'the-man-inside-me',
                'title': 'The Man Inside Me',
                'ext': 'mp4'
            }
        },
        {
            'url': 'https://www8.doramasmp4.com/the-painter-of-the-wind-capitulo-1/',
            'info_dict': {
                'id': 'the-painter-of-the-wind-capitulo-1',
                'title': 'The Painter of the Wind Capítulo 1 sub español',
                'ext': 'mp4'
            }
        },
        {
            'url': 'https://www8.doramasmp4.com/princess-silver-capitulo-1/',
            'info_dict': {
                'id': 'princess-silver-capitulo-1',
                'title': 'Princess Silver Capítulo 1 sub español',
                'ext': 'mp4'
            }
        },
        {
            'url': 'https://www8.doramasmp4.com/the-painter-of-the-wind/',
            'info_dict': {
                'id': 'the-painter-of-the-wind',
            },
            'playlist_count': 20
        },
        {
            'url': 'https://www8.doramasmp4.com/princess-silver/',
            'info_dict': {
                'id': 'princess-silver',
            },
            'playlist_count': 58
        }
    ]

    def _find_sources(self, content, video_id):
        videos = self._parse_json(
            self._html_search_regex(
                r'var sources = (?P<array>.*);', content, 'url'
            ), video_id
        )
        return next(iter(videos), {}).get('file')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage).replace(' | Doramasmp4.com', '')

        try:
            is_playlist = self._html_search_meta(
                'article:section', webpage
            ) == 'tv'
        except ExtractorError:
            is_playlist = False

        if is_playlist:
            matches = re.findall(
                r'<a\s+(?:[^>]*?\s+)?href=(")?(?P<url>.+?{}.*?)\1'.format(
                    video_id
                ),
                webpage
            )
            entries = []
            for match in matches:
                entries.append(self.url_result(match[1], ie='Doramasmp4'))

            return self.playlist_result(entries, playlist_id=video_id)
        else:
            original = self._html_search_regex(
                r'data-link\s*=\s*"(?P<url>.+?)"', webpage, 'url'
            )
            first = self._download_webpage(original, video_id)
            second = self._download_webpage(
                self._html_search_regex(
                    r'src\s*=\s*"(?P<url>.+?)"', first, 'url'
                ), video_id, headers={'referer': clean_html(original)}
            )
            if 'var sources' in second:
                url = self._request_webpage(
                    self._find_sources(second, video_id), video_id
                ).geturl()
            else:
                third = self._download_webpage(
                    self._html_search_regex(
                        r'window.location.href = \'(?P<url>.*)\'', second, 'url'
                    ), video_id
                )
                url = self._find_sources(third, video_id)

            return {
                'title': title,
                'id': video_id,
                'url': url
            }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    base_url,
    remove_start,
    urljoin,
)


class VisirMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?visir\.is/section(?:/media)?/.+?fileid=(?P<id>[^/]+)$'
    _TESTS = [{
        'url': 'http://www.visir.is/section/MEDIA99&fileid=CLP51729',
        'md5': '1486324696d1b9f30fcea985a7922f2c',
        'info_dict': {
            'id': 'CLP51729',
            'display_id': 'CLP51729',
            'ext': 'mp4',
            'title': 'Gu\u00f0j\u00f3n: Mj\u00f6g j\u00e1kv\u00e6\u00f0ur \u00e1 framhaldi\u00f0',
            'description': None,
            'thumbnail': 'http://www.visir.is/apps/pbcsi.dll/urlget?url=/clips/51729_3.jpg'
        },
    }, {
        'url': 'http://www.visir.is/section/MEDIA99&fileid=CLP45905',
        'info_dict': {
            'id': 'CLP45905',
            'display_id': 'CLP45905',
            'ext': 'mp4',
            'title': 'Eva Laufey - Nau\u00f0synlegt a\u00f0 b\u00f6rn f\u00e1i a\u00f0 koma n\u00e1l\u00e6gt matarger\u00f0',
            'description': 'md5:24422433a08d270a3690d149edf113b8',
            'thumbnail': 'http://www.visir.is/apps/pbcsi.dll/urlget?url=/clips/45905_3.jpg',
        },
        'params': {
            'skip_download': True,
        },
    }]

    @staticmethod
    def _extract_urls(webpage):
        media_base_url = 'http://www.visir.is/section/media/?template=iplayer&fileid=%s'
        video_ids = [media_base_url % m.group('id') for m in re.finditer(
            r'App\.Player\.Init\(\{[^\}]*Type:\s*\'(?:audio|video)\'[^\}]+FileId:\s*\'(?P<id>.+?)\'[^\}]+Host:\s*\'visirvod\.365cdn\.is\'',
            webpage)]
        return video_ids

    def _extract_formats(self, filename, video_id, media_type):
        playlist_url = 'http://visirvod.365cdn.is/hls-vod/_definst_/mp4:%s/playlist.m3u8' % filename
        if media_type == 'video':
            formats = self._extract_wowza_formats(
                playlist_url, video_id, skip_protocols=['dash'])
        else:
            formats = self._extract_wowza_formats(
                playlist_url, video_id, skip_protocols=['dash', 'f4m', 'm3u8'])
        self._sort_formats(formats)
        return formats

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        regex_pattern = r'App\.Player\.Init\s*\(\s*\{[^\}]*%s:[^\}]*?\'(.+?)\''
        video_id = self._search_regex(
            regex_pattern % 'FileId',
            webpage, 'video id')
        filename = self._search_regex(
            regex_pattern % 'File',
            webpage, 'filename')
        media_type = self._search_regex(
            regex_pattern % 'Type',
            webpage, 'media type')

        formats = self._extract_formats(filename, video_id, media_type)

        title = self._search_regex(
            regex_pattern % 'Title',
            webpage, 'video title', default=None)
        if not title:
            title = self._og_search_title(webpage)
            if title:
                title = remove_start(title, 'Vísir -').strip()

        description = self._og_search_description(webpage, default=None)

        thumbnail = self._search_regex(
            regex_pattern % '(?:I|i)mage',
            webpage, 'video title', default=None)
        if thumbnail:
            if thumbnail.startswith('/'):
                thumbnail = urljoin(base_url(url), thumbnail)
        else:
            thumbnail = self._og_search_thumbnail(webpage, default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }

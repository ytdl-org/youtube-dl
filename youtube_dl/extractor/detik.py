# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class DuaPuluhDetikIE(InfoExtractor):
    _VALID_URL = r'https?://20\.detik\.com/embed/(?P<video_id>\d+)'
    IE_NAME = '20detik'
    _TESTS = [{
        'url': 'https://20.detik.com/embed/180403001?autostart=1',
        'info_dict': {
            'id': '180403001',
            'title': 'Dahsyatnya Rudal Anti-balistik yang Diuji Coba Rusia',
            'description': 'md5:909c645cc494f5d9d7089963c13a695d',
            'thumbnail': r're:^https?://.*\.jpg(\?.*)?$',
            'ext': 'mp4'
        }
    }, {
        'url': 'https://20.detik.com/embed/180326044',
        'info_dict': {
            'id': '180326044',
            'title': 'md5:204cbc0b3b51b701ee9dc6a502f1e17b',
            'description': 'md5:227d860110eda61876b243e23fe38538',
            'thumbnail': r're:^https?://.*\.jpg(\?.*)?$',
            'ext': 'mp4'
        }
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [m.group('url') for m in re.finditer(
            r'<iframe[^>]+?src\s*=\s*(["\'])(?P<url>https?://20\.detik\.com/embed/\d+).+?\1',
            webpage)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)
        m3u8_url = self._html_search_regex(
            r'["\']videoUrl["\']\s*:\s*["\'](?P<m3u8_url>.+)["\']',
            webpage, 'm3u8_url')

        if m3u8_url is None:
            raise ExtractorError('Video not found')

        title = self._og_search_title(webpage)
        description = self._og_search_description(
            webpage, default='')
        thumbnail = self._og_search_property(
            'image', webpage)
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats
        }

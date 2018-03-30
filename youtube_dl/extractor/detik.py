# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class DuaPuluhDetikIE(InfoExtractor):
    _VALID_URL = r'https?://20\.detik\.com/[^/]+/(?P<date>\d+)-(?P<id>\d+)/(?P<slug>[^/?#&]+)'
    IE_NAME = '20detik'
    _TESTS = [{
        'url': 'https://20.detik.com/detikflash/20180328-180328002/dramatis-polisi-selamatkan-pria-yang-coba-bunuh-diri',
        'info_dict': {
            'id': '180328002',
            'display_id': '20180328-180328002',
            'slug': 'dramatis-polisi-selamatkan-pria-yang-coba-bunuh-diri',
            'upload_date': '20180328',
            'title': 'md5:92c18d820d8937f259007e9c6ce40e6b',
            'description': 'md5:3953164fc1746eb98aa3729140f9b5b8',
            'thumbnail': r're:^https?://.*\.jpg(\?.*)?$',
            'ext': 'mp4'
        }
    }, {
        'url': 'https://20.detik.com/e-flash/20180328-180328009/unboxing-huawei-p20-pro-',
        'only_matching': True
    }, {
        'url': 'https://20.detik.com/otobuzz/20180228-180228081/primadona-baru-di-kelas-low-mpv',
        'only_matching': True
    }, {
        'url': 'https://20.detik.com/sport-buzz/20180328-180328013/messi-kabur-melihat-argentina-dibantai-spanyol',
        'only_matching': True
    }, {
        'url': 'https://20.detik.com/piala-dunia-2018/20180328-180328005/gary-lineker-dan-memori-piala-dunia-1986',
        'only_matching': True
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        upload_date, video_id = mobj.group('date', 'id')
        embed_url = 'https://20.detik.com/embed/%s' % video_id
        display_id = "%s-%s" % (upload_date, video_id)
        webpage = self._download_webpage(embed_url, video_id)
        m3u8_url = self._html_search_regex(
            r'''["\']videoUrl["\']\s*:\s*["\'](?P<m3u8_url>.*?)["\']''',
            webpage, 'm3u8_url', group='m3u8_url', default='')
        if len(m3u8_url) == 0:
            raise ExtractorError('Video not found')
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_property('image', webpage)
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'upload_date': upload_date,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'ext': 'mp4',
            'formats': formats
        }

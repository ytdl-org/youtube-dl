# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class SportBoxIE(InfoExtractor):
    _VALID_URL = r'https?://news\.sportbox\.ru/Vidy_sporta/(?:[^/]+/)+spbvideo_NI\d+_(?P<display_id>.+)'
    _TESTS = [
        {
            'url': 'http://news.sportbox.ru/Vidy_sporta/Avtosport/Rossijskij/spbvideo_NI483529_Gonka-2-zaezd-Obyedinenniy-2000-klassi-Turing-i-S',
            'md5': 'ff56a598c2cf411a9a38a69709e97079',
            'info_dict': {
                'id': '80822',
                'ext': 'mp4',
                'title': 'Гонка 2  заезд ««Объединенный 2000»: классы Туринг и Супер-продакшн',
                'description': 'md5:81715fa9c4ea3d9e7915dc8180c778ed',
                'thumbnail': 're:^https?://.*\.jpg$',
                'timestamp': 1411896237,
                'upload_date': '20140928',
                'duration': 4846,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        }, {
            'url': 'http://news.sportbox.ru/Vidy_sporta/billiard/spbvideo_NI486287_CHempionat-mira-po-dinamichnoy-piramide-4',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'src="/vdl/player/media/(\d+)"', webpage, 'video id')

        player = self._download_webpage(
            'http://news.sportbox.ru/vdl/player/media/%s' % video_id,
            display_id, 'Downloading player webpage')

        hls = self._search_regex(
            r"var\s+original_hls_file\s*=\s*'([^']+)'", player, 'hls file')

        formats = self._extract_m3u8_formats(hls, display_id, 'mp4')

        title = self._html_search_regex(
            r'<h1 itemprop="name">([^<]+)</h1>', webpage, 'title')
        description = self._html_search_regex(
            r'(?s)<div itemprop="description">(.+?)</div>', webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = parse_iso8601(self._search_regex(
            r'<span itemprop="uploadDate">([^<]+)</span>', webpage, 'timestamp', fatal=False))
        duration = parse_duration(self._html_search_regex(
            r'<meta itemprop="duration" content="PT([^"]+)">', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }

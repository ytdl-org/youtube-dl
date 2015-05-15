# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class SportBoxIE(InfoExtractor):
    _VALID_URL = r'https?://news\.sportbox\.ru/(?:[^/]+/)+spbvideo_NI\d+_(?P<display_id>.+)'
    _TESTS = [{
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
    }, {
        'url': 'http://news.sportbox.ru/video/no_ads/spbvideo_NI536574_V_Novorossijske_proshel_detskij_turnir_Pole_slavy_bojevoj?ci=211355',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        player = self._search_regex(
            r'src="/?(vdl/player/[^"]+)"', webpage, 'player')

        title = self._html_search_regex(
            r'<h1 itemprop="name">([^<]+)</h1>', webpage, 'title')
        description = self._html_search_regex(
            r'(?s)<div itemprop="description">(.+?)</div>',
            webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = parse_iso8601(self._search_regex(
            r'<span itemprop="uploadDate">([^<]+)</span>',
            webpage, 'timestamp', fatal=False))
        duration = parse_duration(self._html_search_regex(
            r'<meta itemprop="duration" content="PT([^"]+)">',
            webpage, 'duration', fatal=False))

        return {
            '_type': 'url_transparent',
            'url': compat_urlparse.urljoin(url, '/%s' % player),
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
        }


class SportBoxEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://news\.sportbox\.ru/vdl/player(?:/[^/]+/|\?.*?\bn?id=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://news.sportbox.ru/vdl/player/ci/211355',
        'info_dict': {
            'id': '211355',
            'ext': 'mp4',
            'title': 'В Новороссийске прошел детский турнир «Поле славы боевой»',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://news.sportbox.ru/vdl/player?nid=370908&only_player=1&autostart=false&playeri=2&height=340&width=580',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        hls = self._search_regex(
            r"sportboxPlayer\.jwplayer_common_params\.file\s*=\s*['\"]([^'\"]+)['\"]",
            webpage, 'hls file')

        formats = self._extract_m3u8_formats(hls, video_id, 'mp4')

        title = self._search_regex(
            r'sportboxPlayer\.node_title\s*=\s*"([^"]+)"', webpage, 'title')

        thumbnail = self._search_regex(
            r'sportboxPlayer\.jwplayer_common_params\.image\s*=\s*"([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

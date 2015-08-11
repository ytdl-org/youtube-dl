# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    unified_strdate,
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
            'description': 'md5:3d72dc4a006ab6805d82f037fdc637ad',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20140928',
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
            [r'"nodetitle"\s*:\s*"([^"]+)"', r'class="node-header_{1,2}title">([^<]+)'],
            webpage, 'title')
        description = self._og_search_description(webpage) or self._html_search_meta(
            'description', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)
        upload_date = unified_strdate(self._html_search_meta(
            'dateCreated', webpage, 'upload date'))

        return {
            '_type': 'url_transparent',
            'url': compat_urlparse.urljoin(url, '/%s' % player),
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
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

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src="(https?://news\.sportbox\.ru/vdl/player[^"]+)"',
            webpage)

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
            webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

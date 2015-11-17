# encoding: utf-8
from __future__ import unicode_literals

import time

from .common import InfoExtractor
from ..utils import int_or_none


class DPlayIE(InfoExtractor):
    _VALID_URL = r'http://www\.dplay\.se/[^/]+/(?P<id>[^/?#]+)'

    _TEST = {
        'url': 'http://www.dplay.se/nugammalt-77-handelser-som-format-sverige/season-1-svensken-lar-sig-njuta-av-livet/',
        'info_dict': {
            'id': '3172',
            'ext': 'mp4',
            'display_id': 'season-1-svensken-lar-sig-njuta-av-livet',
            'title': 'Svensken lär sig njuta av livet',
            'duration': 2650,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'data-video-id="(\d+)"', webpage, 'video id')

        info = self._download_json(
            'http://www.dplay.se/api/v2/ajax/videos?video_id=' + video_id,
            video_id)['data'][0]

        self._set_cookie(
            'secure.dplay.se', 'dsc-geo',
            '{"countryCode":"NL","expiry":%d}' % ((time.time() + 20 * 60) * 1000))
        # TODO: consider adding support for 'stream_type=hds', it seems to
        # require setting some cookies
        manifest_url = self._download_json(
            'https://secure.dplay.se/secure/api/v2/user/authorization/stream/%s?stream_type=hls' % video_id,
            video_id, 'Getting manifest url for hls stream')['hls']
        formats = self._extract_m3u8_formats(
            manifest_url, video_id, ext='mp4', entry_protocol='m3u8_native')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'formats': formats,
            'duration': int_or_none(info.get('video_metadata_length'), scale=1000),
        }

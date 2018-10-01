# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ServusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?servus\.com/(?:at|de)/p/[^/]+/(?P<id>AA-\w+|\d+-\d+)'
    _TESTS = [{
        'url': 'https://www.servus.com/de/p/Die-Gr%C3%BCnen-aus-Sicht-des-Volkes/AA-1T6VBU5PW1W12/',
        'md5': '046dee641cda1c4cabe13baef3be2c1c',
        'info_dict': {
            'id': 'AA-1T6VBU5PW1W12',
            'ext': 'mp4',
            'title': 'Die Grünen aus Volkssicht',
            'description': 'md5:052b5da1cb2cd7d562ef1f19be5a5cba',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'https://www.servus.com/at/p/Wie-das-Leben-beginnt/1309984137314-381415152/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        formats = self._extract_m3u8_formats(
            'https://stv.rbmbtnx.net/api/v1/manifests/%s.m3u8' % video_id,
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }

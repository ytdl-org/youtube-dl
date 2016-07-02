# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
)


class LA7IE(InfoExtractor):
    IE_NAME = 'la7.it'
    _VALID_URL = r'''(?x)(https?://)?(?:
        (?:www\.)?la7\.it/([^/]+)/(?:rivedila7|video)/|
        tg\.la7\.it/repliche-tgla7\?id=
    )(?P<id>.+)'''

    _TESTS = [{
        # 'src' is a plain URL
        'url': 'http://www.la7.it/crozza/video/inccool8-02-10-2015-163722',
        'md5': '6054674766e7988d3e02f2148ff92180',
        'info_dict': {
            'id': 'inccool8-02-10-2015-163722',
            'ext': 'mp4',
            'title': 'Inc.Cool8',
            'description': 'Benvenuti nell\'incredibile mondo della INC. COOL. 8. dove “INC.” sta per “Incorporated” “COOL” sta per “fashion” ed Eight sta per il gesto  atletico',
            'thumbnail': 're:^https?://.*',
        },
    }, {
        # 'src' is a dictionary
        'url': 'http://tg.la7.it/repliche-tgla7?id=189080',
        'md5': '6b0d8888d286e39870208dfeceaf456b',
        'info_dict': {
            'id': '189080',
            'ext': 'mp4',
            'title': 'TG LA7',
        },
    }, {
        'url': 'http://www.la7.it/omnibus/rivedila7/omnibus-news-02-07-2016-189077',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        player_data = self._parse_json(
            self._search_regex(r'videoLa7\(({[^;]+})\);', webpage, 'player data'),
            video_id, transform_source=js_to_json)

        source = player_data['src']
        source_urls = source.values() if isinstance(source, dict) else [source]

        formats = []
        for source_url in source_urls:
            ext = determine_ext(source_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls'))
            else:
                formats.append({
                    'url': source_url,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': player_data['title'],
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': player_data.get('poster'),
            'formats': formats,
        }

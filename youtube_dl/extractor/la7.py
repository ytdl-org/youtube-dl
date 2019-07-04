# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    smuggle_url,
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
        'md5': '8b613ffc0c4bf9b9e377169fc19c214c',
        'info_dict': {
            'id': 'inccool8-02-10-2015-163722',
            'ext': 'mp4',
            'title': 'Inc.Cool8',
            'description': 'Benvenuti nell\'incredibile mondo della INC. COOL. 8. dove “INC.” sta per “Incorporated” “COOL” sta per “fashion” ed Eight sta per il gesto  atletico',
            'thumbnail': 're:^https?://.*',
            'uploader_id': 'kdla7pillole@iltrovatore.it',
            'timestamp': 1443814869,
            'upload_date': '20151002',
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
            self._search_regex(
                [r'(?s)videoParams\s*=\s*({.+?});', r'videoLa7\(({[^;]+})\);'],
                webpage, 'player data'),
            video_id, transform_source=js_to_json)

        return {
            '_type': 'url_transparent',
            'url': smuggle_url('kaltura:103:%s' % player_data['vid'], {
                'service_url': 'http://kdam.iltrovatore.it',
            }),
            'id': video_id,
            'title': player_data['title'],
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': player_data.get('poster'),
            'ie_key': 'Kaltura',
        }

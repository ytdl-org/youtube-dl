# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    urljoin,
)


class ReshetIE(InfoExtractor):
    _VALID_URL = r'https?://13tv\.co\.il/item/(?P<category>[^/]+)/(?P<series>[^/]+)/(?P<season>[^/]+)/(?P<type>[^/]+)/(?P<id>[^/]+)/?'

    _TEST = {
        'url': 'https://13tv.co.il/item/entertainment/gav-hauma/season-10/episodes/jz1a1-1028855',
        'note': 'Test brightcove URL extraction',
        'info_dict': {
            'id': '6015811232001',
            'ext': 'mp4',
            'timestamp': 1553031049,
            'title': 'entertainment-gav-hauma-season-10-episodes-10-full_au8bmF8M',
            'uploader_id': '1551111274001',
            'upload_date': '20190319',
        }
    }

    def _real_extract(self, url):
        reshet_id = self._match_id(url)

        page = self._download_webpage(url, reshet_id)
        data = self._parse_json(re.search(r'var initial_data = (.*?);\n', page).group(1), reshet_id)
        item = data['items'][str(data['curItem'])]
        brightcove_id = item['video']['videoID']

        main_js_url = urljoin(url, re.search(r'<script type="text/javascript" src="(/[^"]*/main.[a-f0-9]+\.js)">', page).group(1))
        js = self._download_webpage(main_js_url, reshet_id)
        acctId, playerId = re.search('accountID:[^,]*"([0-9]+)",playerID:[^,]*"([^"]+)",', js).groups()

        brightcove_url = 'http://players.brightcove.net/%s/%s_default/index.html?videoId=%s' % (acctId, playerId, brightcove_id)

        return self.url_result(brightcove_url, 'BrightcoveNew')

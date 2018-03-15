# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DmdaMediaIE(InfoExtractor):

    _VALID_URL = r'https?://(?:www\.)?dmdamedia\.hu/(?P<id>[^/]+).*'
    _TEST = {
        'url': 'http://dmdamedia.hu/vasott_szulok/3.evad/3.resz?a=2',
        'info_dict': {
            'id': '9tgrrmz55f7q',
            'ext': 'mp4',
            'title': 'Vásott szülők 3. Évad 3. Rész Online dmdamedia.hu',
        }
    }

    def _real_extract(self, url):
        url_match = re.match(self._VALID_URL, url)
        video_id = url_match.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title', default=None)
        url = self._html_search_regex(r'<iframe[^>]*?src=\"(.*?)\"', webpage, 'url')

        return {
            'id': video_id,
            'title': title,
            'url': url,
            '_type': 'url_transparent'
        }

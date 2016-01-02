# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class Min20IE(InfoExtractor):
    _VALID_URL = r'http://www\.20min\.ch/.+?-(?P<id>[0-9]+)$'
    _TEST = {
        'url': 'http://www.20min.ch/schweiz/news/story/-Wir-muessen-mutig-nach-vorne-schauen--22050469',
        'md5': 'cd4cbb99b94130cff423e967cd275e5e',
        'info_dict': {
            'id': '22050469',
            'ext': 'flv',
            'title': '«Wir müssen mutig nach vorne schauen»',
            'description': 'Kein Land sei innovativer als die Schweiz, sagte Johann Schneider-Ammann in seiner Neujahrsansprache. Das Land müsse aber seine Hausaufgaben machen.',
            'thumbnail': 'http://www.20min.ch/images/content/2/2/0/22050469/10/teaserbreit.jpg'
        }
    }

    # location of the flv videos, can't be extracted from the web page
    _BASE_URL = "http://flv-rr.20min-tv.ch/videos/"

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1><span>(.+?)</span></h1>', webpage, 'title')
        flash_id = self._search_regex(r"so\.addVariable\(\"file1\",\"([0-9]+)\"\)", webpage, 'flash_id')

        description = self._html_search_regex(r'<meta name="description" content="(.+?)" />', webpage, 'description')
        thumbnail = self._html_search_regex(r'<meta property="og:image" content="(.+?)" />', webpage, 'thumbnail')
        url = self._BASE_URL + flash_id + "m.flv"

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail
        }

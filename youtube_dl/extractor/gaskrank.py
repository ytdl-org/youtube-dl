# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class GaskrankIE(InfoExtractor):
    IE_NAME = 'Gaskrank'
    _VALID_URL = r'(http.?://)www\.gaskrank\.tv/tv/.*?/(?P<id>.*?)\.htm.?'
    _TEST = {
        'url': 'http://www.gaskrank.tv/tv/motorradtreffen/elefantentreffen-2017-mit-suzuki-gsx-r-750-auf-winterreifen.htm',
        'md5': '23c91b49a5d599430824e586854081dd',
        'info_dict': {
            'id': 'elefantentreffen-2017-mit-suzuki-gsx-r-750-auf-winterreifen',
            'ext': 'mp4',
            'title': 'Elefantentreffen 2017 mit Suzuki GSX-R 750 auf Winterreifen '
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        url_medium_qual = self._html_search_regex(r'0: { src:"(.*?)", type:', webpage, 'url')
        url_high_qual = self._html_search_regex(r'1: { src:"(.*?)", type:', webpage, 'url')

        return {
            'id': video_id,
            'title': title,
            'url': url_high_qual
        }


# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .youtube import YoutubeIE


class JadoreCettePubIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?jadorecettepub\.com/[0-9]{4}/[0-9]{2}/(?P<id>.*?)\.html'

    _TEST = {
        'url': 'http://www.jadorecettepub.com/2010/12/star-wars-massacre-par-les-japonais.html',
        'md5': '401286a06067c70b44076044b66515de',
        'info_dict': {
            'id': 'jLMja3tr7a4',
            'ext': 'mp4',
            'title': 'La pire utilisation de Star Wars',
            'description': "Jadorecettepub.com vous a gratifié de plusieurs pubs géniales utilisant Star Wars et Dark Vador plus particulièrement... Mais l'heure est venue de vous proposer une version totalement massacrée, venue du Japon.  Quand les Japonais détruisent l'image de Star Wars pour vendre du thon en boite, ça promet...",
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_regex(
            r'<span style="font-size: x-large;"><b>(.*?)</b></span>',
            webpage, 'title')
        description = self._html_search_regex(
            r'(?s)<div id="fb-root">(.*?)<script>', webpage, 'description',
            fatal=False)
        real_url = self._search_regex(
            r'\[/postlink\](.*)endofvid', webpage, 'video URL')
        video_id = YoutubeIE.extract_id(real_url)

        return {
            '_type': 'url_transparent',
            'url': real_url,
            'id': video_id,
            'title': title,
            'description': description,
        }

# coding: utf-8

import json
import re

from .common import InfoExtractor

class TF1IE(InfoExtractor):
    """TF1 uses the wat.tv player."""
    _VALID_URL = r'http://videos\.tf1\.fr/.*-(.*?)\.html'
    _TEST = {
        u'url': u'http://videos.tf1.fr/auto-moto/citroen-grand-c4-picasso-2013-presentation-officielle-8062060.html',
        u'file': u'10635995.mp4',
        u'md5': u'2e378cc28b9957607d5e88f274e637d8',
        u'info_dict': {
            u'title': u'Citroën Grand C4 Picasso 2013 : présentation officielle',
            u'description': u'Vidéo officielle du nouveau Citroën Grand C4 Picasso, lancé à l\'automne 2013.',
        },
        u'skip': u'Sometimes wat serves the whole file with the --test option',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        id = mobj.group(1)
        webpage = self._download_webpage(url, id)
        embed_url = self._html_search_regex(r'"(https://www.wat.tv/embedframe/.*?)"',
                                webpage, 'embed url')
        embed_page = self._download_webpage(embed_url, id, u'Downloading embed player page')
        wat_id = self._search_regex(r'UVID=(.*?)&', embed_page, 'wat id')
        wat_info = self._download_webpage('http://www.wat.tv/interface/contentv3/%s' % wat_id, id, u'Downloading Wat info')
        wat_info = json.loads(wat_info)['media']
        wat_url = wat_info['url']
        return self.url_result(wat_url, 'Wat')

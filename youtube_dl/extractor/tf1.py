# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TF1IE(InfoExtractor):
    """TF1 uses the wat.tv player."""
    _VALID_URL = r'http://videos\.tf1\.fr/.*-(?P<id>.*?)\.html'
    _TEST = {
        'url': 'http://videos.tf1.fr/auto-moto/citroen-grand-c4-picasso-2013-presentation-officielle-8062060.html',
        'info_dict': {
            'id': '10635995',
            'ext': 'mp4',
            'title': 'Citroën Grand C4 Picasso 2013 : présentation officielle',
            'description': 'Vidéo officielle du nouveau Citroën Grand C4 Picasso, lancé à l\'automne 2013.',
        },
        'params': {
            # Sometimes wat serves the whole file with the --test option
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        embed_url = self._html_search_regex(
            r'"(https://www.wat.tv/embedframe/.*?)"', webpage, 'embed url')
        embed_page = self._download_webpage(embed_url, video_id,
                                            'Downloading embed player page')
        wat_id = self._search_regex(r'UVID=(.*?)&', embed_page, 'wat id')
        wat_info = self._download_json(
            'http://www.wat.tv/interface/contentv3/%s' % wat_id, video_id)
        return self.url_result(wat_info['media']['url'], 'Wat')

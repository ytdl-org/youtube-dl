# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TweakersIE(InfoExtractor):
    _VALID_URL = r'https?://tweakers\.net/video/(?P<id>[0-9]+).*'
    _TEST = {
        'url': 'https://tweakers.net/video/9926/new-nintendo-3ds-xl-op-alle-fronten-beter.html',
        'md5': 'f7f7f3027166a7f32f024b4ae6571ced',
        'info_dict': {
            'id': '9926',
            'ext': 'mp4',
            'title': 'New-Nintendo-3Ds-Xl-Op-Alle-Fronten-Beter',
        }
    }

    def _real_extract(self, url):
        splitted_url = re.split('.html|/', url)
        del splitted_url[-1]  # To remove extra '/' at the end
        video_id = splitted_url[4]
        title = splitted_url[5].title()  # Retrieve title for URL and capitalize
        splitted_url[3] = splitted_url[3] + '/player'  # Add /player to get the player page
        player_url = '/'.join(splitted_url) + '.html'
        player_page = self._download_webpage(player_url, video_id)

        return {
            'id': video_id,
            'ext': 'mp4',
            'title': title,
            'url': re.findall('http.*mp4', player_page)[0],
        }

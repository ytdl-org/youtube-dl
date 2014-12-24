from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class DefenseGouvFrIE(InfoExtractor):
    IE_NAME = 'defense.gouv.fr'
    _VALID_URL = (r'http://.*?\.defense\.gouv\.fr/layout/set/'
                  r'ligthboxvideo/base-de-medias/webtv/(.*)')

    _TEST = {
        'url': 'http://www.defense.gouv.fr/layout/set/ligthboxvideo/base-de-medias/webtv/attaque-chimique-syrienne-du-21-aout-2013-1',
        'file': '11213.mp4',
        'md5': '75bba6124da7e63d2d60b5244ec9430c',
        "info_dict": {
            "title": "attaque-chimique-syrienne-du-21-aout-2013-1"
        }
    }

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        video_id = self._search_regex(
            r"flashvars.pvg_id=\"(\d+)\";",
            webpage, 'ID')

        json_url = ('http://static.videos.gouv.fr/brightcovehub/export/json/'
                    + video_id)
        info = self._download_webpage(json_url, title,
                                      'Downloading JSON config')
        video_url = json.loads(info)['renditions'][0]['url']

        return {'id': video_id,
                'ext': 'mp4',
                'url': video_url,
                'title': title,
                }

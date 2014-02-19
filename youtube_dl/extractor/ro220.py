from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    compat_parse_qs,
)


class Ro220IE(InfoExtractor):
    IE_NAME = '220.ro'
    _VALID_URL = r'(?x)(?:https?://)?(?:www\.)?220\.ro/(?P<category>[^/]+)/(?P<shorttitle>[^/]+)/(?P<video_id>[^/]+)'
    _TEST = {
        "url": "http://www.220.ro/sport/Luati-Le-Banii-Sez-4-Ep-1/LYV6doKo7f/",
        'file': 'LYV6doKo7f.mp4',
        'md5': '03af18b73a07b4088753930db7a34add',
        'info_dict': {
            "title": "Luati-le Banii sez 4 ep 1",
            "description": "Iata-ne reveniti dupa o binemeritata vacanta. Va astept si pe Facebook cu pareri si comentarii.",
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)
        flashVars_str = self._search_regex(
            r'<param name="flashVars" value="([^"]+)"',
            webpage, 'flashVars')
        flashVars = compat_parse_qs(flashVars_str)

        return {
            '_type': 'video',
            'id': video_id,
            'ext': 'mp4',
            'url': flashVars['videoURL'][0],
            'title': flashVars['title'][0],
            'description': clean_html(flashVars['desc'][0]),
            'thumbnail': flashVars['preview'][0],
        }

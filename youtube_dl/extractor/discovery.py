from __future__ import unicode_literals

import re
import json
from .common import InfoExtractor


class DiscoveryIE(InfoExtractor):
    _VALID_URL = r'http://dsc\.discovery\.com\/[a-zA-Z0-9\-]*/[a-zA-Z0-9\-]*/videos/(?P<id>[a-zA-Z0-9\-]*)(.htm)?'
    _TEST = {
        'url': 'http://dsc.discovery.com/tv-shows/mythbusters/videos/mission-impossible-outtakes.htm',
        'file': 'mission-impossible-outtakes.mp4',
        'md5': 'e12614f9ee303a6ccef415cb0793eba2',
        'info_dict': {
            'title': 'MythBusters: Mission Impossible Outtakes'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(
            r'(?<=\"name\": ")(?P<title>.*?)(?=\"\,)', webpage, r'Filename')
        duration = int(self._search_regex(
            r'(?<=\"duration\"\: )(?P<duration>.*?)(?=,)', webpage, r'Duration'))
        formats_raw = self._search_regex(
            r'(?<=\"mp4\":)(.*?)(}])', webpage, r'formats') + '}]'
        formats_json = json.loads(formats_raw)
        formats = []
        for f in formats_json:
            formats.append(
                {'url': f['src'], r'ext': r'mp4', 'tbr': int(f['bitrate'][:-1])})

        return {
            'id': video_id,
            'duration': duration,
            'title': title,
            'formats': formats
        }

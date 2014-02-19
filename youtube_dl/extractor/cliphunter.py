from __future__ import unicode_literals

import re

from .common import InfoExtractor


translation_table = {
    'a': 'h', 'd': 'e', 'e': 'v', 'f': 'o', 'g': 'f', 'i': 'd', 'l': 'n',
    'm': 'a', 'n': 'm', 'p': 'u', 'q': 't', 'r': 's', 'v': 'p', 'x': 'r',
    'y': 'l', 'z': 'i',
    '$': ':', '&': '.', '(': '=', '^': '&', '=': '/',
}


class CliphunterIE(InfoExtractor):
    IE_NAME = 'cliphunter'

    _VALID_URL = r'''(?x)http://(?:www\.)?cliphunter\.com/w/
        (?P<id>[0-9]+)/
        (?P<seo>.+?)(?:$|[#\?])
    '''
    _TEST = {
        'url': 'http://www.cliphunter.com/w/1012420/Fun_Jynx_Maze_solo',
        'file': '1012420.flv',
        'md5': '15e7740f30428abf70f4223478dc1225',
        'info_dict': {
            'title': 'Fun Jynx Maze solo',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        pl_fiji = self._search_regex(
            r'pl_fiji = \'([^\']+)\'', webpage, 'video data')
        pl_c_qual = self._search_regex(
            r'pl_c_qual = "(.)"', webpage, 'video quality')
        video_title = self._search_regex(
            r'mediaTitle = "([^"]+)"', webpage, 'title')

        video_url = ''.join(translation_table.get(c, c) for c in pl_fiji)

        formats = [{
            'url': video_url,
            'format_id': pl_c_qual,
        }]

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
        }

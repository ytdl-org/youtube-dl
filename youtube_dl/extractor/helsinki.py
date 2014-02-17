# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class HelsinkiIE(InfoExtractor):
    _VALID_URL = r'https?://video\.helsinki\.fi/Arkisto/flash\.php\?id=(?P<id>\d+)'
    _TEST = {
        'url': 'http://video.helsinki.fi/Arkisto/flash.php?id=20258',
        'md5': 'cd829201b890905682eb194cbdea55d7',
        'info_dict': {
            'id': '20258',
            'ext': 'mp4',
            'title': 'Tietotekniikkafoorumi-iltapäivä',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        vid = mobj.group('id')
        webpage = self._download_webpage(url, vid)
        formats = []
        mobj = re.search('file=((\w+):[^&]+)', webpage)
        if mobj: formats.append({
            'ext': mobj.group(2),
            'play_path': mobj.group(1),
            'url': 'rtmp://flashvideo.it.helsinki.fi/vod/',
            'player_url': 'http://video.helsinki.fi/player.swf',
            'format_note': 'sd'
        })

        mobj = re.search('hd\.file=((\w+):[^&]+)', webpage)
        if mobj: formats.append({
            'ext': mobj.group(2),
            'play_path': mobj.group(1),
            'url': 'rtmp://flashvideo.it.helsinki.fi/vod/',
            'player_url': 'http://video.helsinki.fi/player.swf',
            'format_note': 'hd'
        })

        return {
            'id': vid,
            'title': self._og_search_title(webpage).replace('Video: ', ''),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats
        }

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class HelsinkiIE(InfoExtractor):
    IE_DESC = 'helsinki.fi'
    _VALID_URL = r'https?://video\.helsinki\.fi/Arkisto/flash\.php\?id=(?P<id>\d+)'
    _TEST = {
        'url': 'http://video.helsinki.fi/Arkisto/flash.php?id=20258',
        'info_dict': {
            'id': '20258',
            'ext': 'mp4',
            'title': 'Tietotekniikkafoorumi-iltapäivä',
            'description': 'md5:f5c904224d43c133225130fe156a5ee0',
        },
        'params': {
            'skip_download': True,  # RTMP
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        formats = []

        mobj = re.search(r'file=((\w+):[^&]+)', webpage)
        if mobj:
            formats.append({
                'ext': mobj.group(2),
                'play_path': mobj.group(1),
                'url': 'rtmp://flashvideo.it.helsinki.fi/vod/',
                'player_url': 'http://video.helsinki.fi/player.swf',
                'format_note': 'sd',
                'quality': 0,
            })

        mobj = re.search(r'hd\.file=((\w+):[^&]+)', webpage)
        if mobj:
            formats.append({
                'ext': mobj.group(2),
                'play_path': mobj.group(1),
                'url': 'rtmp://flashvideo.it.helsinki.fi/vod/',
                'player_url': 'http://video.helsinki.fi/player.swf',
                'format_note': 'hd',
                'quality': 1,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage).replace('Video: ', ''),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }

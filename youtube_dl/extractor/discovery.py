from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class DiscoveryIE(InfoExtractor):
    _VALID_URL = r'http://dsc\.discovery\.com\/[a-zA-Z0-9\-]*/[a-zA-Z0-9\-]*/videos/(?P<id>[a-zA-Z0-9\-]*)(.htm)?'
    _TEST = {
        'url': 'http://dsc.discovery.com/tv-shows/mythbusters/videos/mission-impossible-outtakes.htm',
        'file': '614784.mp4',
        'md5': 'e12614f9ee303a6ccef415cb0793eba2',
        'info_dict': {
            'title': 'MythBusters: Mission Impossible Outtakes',
            'description': ('Watch Jamie Hyneman and Adam Savage practice being'
                ' each other -- to the point of confusing Jamie\'s dog -- and '
                'don\'t miss Adam moon-walking as Jamie ... behind Jamie\'s'
                ' back.'),
            'duration': 156,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_list_json = self._search_regex(r'var videoListJSON = ({.*?});',
            webpage, 'video list', flags=re.DOTALL)
        video_list = json.loads(video_list_json)
        info = video_list['clips'][0]
        formats = []
        for f in info['mp4']:
            formats.append(
                {'url': f['src'], r'ext': r'mp4', 'tbr': int(f['bitrate'][:-1])})

        return {
            'id': info['contentId'],
            'title': video_list['name'],
            'formats': formats,
            'description': info['videoCaption'],
            'thumbnail': info.get('videoStillURL') or info.get('thumbnailURL'),
            'duration': info['duration'],
        }

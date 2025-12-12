# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class NBLIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|ott\.)?nbl\.com\.au/(?:tv|en(?:-int)?)/(?P<section>game-replays|highlights|condensed-games|embed)?/?(?P<id>[0-9]+)/?(?P<display_id>.*)'
    _TESTS = [
        {
            'url': 'https://nbl.com.au/tv/highlights/1310086/Perth-Wildcats-vs.-Sydney-Kings---Game-Highlights',
            'md5': '684a1126879371c3137850b8474ae3c8',
            'info_dict': {
                'id': '1310086',
                'ext': 'mp4',
                'title': 'Perth Wildcats vs. Sydney Kings - Game Highlights',
                'description': 'Watch the Game Highlights from Perth Wildcats vs. Sydney Kings, 03/26/2022',
                'display_id': 'Perth-Wildcats-vs.-Sydney-Kings---Game-Highlights',
                'upload_date': '20220326'
            }
        },
        {
            'url': 'https://nbl.com.au/tv/condensed-games/1310087/Perth-Wildcats-vs.-Sydney-Kings---Condensed-Game',
            'md5': '1f9ac9ea04dc4024e50b27593860a782',
            'info_dict': {
                'id': '1310087',
                'ext': 'mp4',
                'title': 'Perth Wildcats vs. Sydney Kings - Condensed Game',
                'description': 'Watch the Condensed Game from Perth Wildcats vs. Sydney Kings, 03/26/2022',
                'display_id': 'Perth-Wildcats-vs.-Sydney-Kings---Condensed-Game',
                'upload_date': '20220326'
            }
        },
        {
            'url': 'https://nbl.com.au/tv/game-replays/1303323/NBL22-Round-17-Replay---Perth-Wildcats-vs-Sydney-Kings',
            'md5': '8505f02156f756e865a1aa80050eb768',
            'info_dict': {
                'id': '1303323',
                'ext': 'mp4',
                'title': 'NBL22 Round 17 Replay - Perth Wildcats vs Sydney Kings',
                'display_id': 'NBL22-Round-17-Replay---Perth-Wildcats-vs-Sydney-Kings',
                'upload_date': '20220326'
            }
        },
        {
            'url': 'https://nbl.com.au/tv/game-replays/1303323',
            'md5': '8505f02156f756e865a1aa80050eb768',
            'info_dict': {
                'id': '1303323',
                'ext': 'mp4',
                'title': 'NBL22 Round 17 Replay - Perth Wildcats vs Sydney Kings',
                'display_id': 'NBL22-Round-17-Replay---Perth-Wildcats-vs-Sydney-Kings',
                'upload_date': '20220326'
            }
        },
        {
            'url': 'https://ott.nbl.com.au/en-int/embed/1303323',
            'md5': '8505f02156f756e865a1aa80050eb768',
            'info_dict': {
                'id': '1303323',
                'ext': 'mp4',
                'title': 'NBL22 Round 17 Replay - Perth Wildcats vs Sydney Kings',
                'display_id': 'NBL22-Round-17-Replay---Perth-Wildcats-vs-Sydney-Kings'
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        mobj = re.match(self._VALID_URL, url)
        if mobj.groupdict().get("section") not in ['game-replays', 'highlights', 'condensed-games']:
            webpage = self._download_webpage('https://ott.nbl.com.au/en-int/embed/' + video_id, video_id)
        else:
            webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title\b[^>]*>\s*(.+?)\s*</title>', webpage, 'title')
        stream_url = self._download_json(
            'https://ott.nbl.com.au/api/v2/content/' + video_id + '/access/hls',
            video_id,
            data=b'',
            headers={
                'Referer': 'https://ott.nbl.com.au/en-int/embed/' + video_id,
                'Origin': 'https://ott.nbl.com.au',
                'Content-Length': '0'
            }
        )['data']['stream']
        formats = self._extract_m3u8_formats(stream_url, video_id, ext='mp4')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'display_id': mobj.groupdict().get('display_id') or title.replace(" ", "-"),
            'upload_date': unified_strdate(self._og_search_property('video:release_date', webpage, 'upload_date', fatal=False, default=None)),
            'formats': formats
        }

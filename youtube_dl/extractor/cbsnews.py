# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class CBSNewsIE(InfoExtractor):
    IE_DESC = 'CBS News'
    _VALID_URL = r'http://(?:www\.)?cbsnews\.com/(?:[^/]+/)+(?P<id>[\da-z_-]+)'

    _TESTS = [
        {
            'url': 'http://www.cbsnews.com/news/tesla-and-spacex-elon-musks-industrial-empire/',
            'info_dict': {
                'id': 'tesla-and-spacex-elon-musks-industrial-empire',
                'ext': 'flv',
                'title': 'Tesla and SpaceX: Elon Musk\'s industrial empire',
                'thumbnail': 'http://beta.img.cbsnews.com/i/2014/03/30/60147937-2f53-4565-ad64-1bdd6eb64679/60-0330-pelley-640x360.jpg',
                'duration': 791,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.cbsnews.com/videos/fort-hood-shooting-army-downplays-mental-illness-as-cause-of-attack/',
            'info_dict': {
                'id': 'fort-hood-shooting-army-downplays-mental-illness-as-cause-of-attack',
                'ext': 'flv',
                'title': 'Fort Hood shooting: Army downplays mental illness as cause of attack',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 205,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_info = json.loads(self._html_search_regex(
            r'(?:<ul class="media-list items" id="media-related-items"><li data-video-info|<div id="cbsNewsVideoPlayer" data-video-player-options)=\'({.+?})\'',
            webpage, 'video JSON info'))

        item = video_info['item'] if 'item' in video_info else video_info
        title = item.get('articleTitle') or item.get('hed')
        duration = item.get('duration')
        thumbnail = item.get('mediaImage') or item.get('thumbnail')

        formats = []
        for format_id in ['RtmpMobileLow', 'RtmpMobileHigh', 'Hls', 'RtmpDesktop']:
            uri = item.get('media' + format_id + 'URI')
            if not uri:
                continue
            fmt = {
                'url': uri,
                'format_id': format_id,
            }
            if uri.startswith('rtmp'):
                play_path = re.sub(
                    r'{slistFilePath}', '',
                    uri.split('<break>')[-1].split('{break}')[-1])
                fmt.update({
                    'app': 'ondemand?auth=cbs',
                    'play_path': 'mp4:' + play_path,
                    'player_url': 'http://www.cbsnews.com/[[IMPORT]]/vidtech.cbsinteractive.com/player/3_3_0/CBSI_PLAYER_HD.swf',
                    'page_url': 'http://www.cbsnews.com',
                    'ext': 'flv',
                })
            elif uri.endswith('.m3u8'):
                fmt['ext'] = 'mp4'
            formats.append(fmt)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }

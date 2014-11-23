from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse,
    ExtractorError,
)


class FiveMinIE(InfoExtractor):
    IE_NAME = '5min'
    _VALID_URL = r'''(?x)
        (?:https?://[^/]*?5min\.com/Scripts/PlayerSeed\.js\?(.*?&)?playList=|
            5min:)
        (?P<id>\d+)
        '''

    _TESTS = [
        {
            # From http://www.engadget.com/2013/11/15/ipad-mini-retina-display-review/
            'url': 'http://pshared.5min.com/Scripts/PlayerSeed.js?sid=281&width=560&height=345&playList=518013791',
            'md5': '4f7b0b79bf1a470e5004f7112385941d',
            'info_dict': {
                'id': '518013791',
                'ext': 'mp4',
                'title': 'iPad Mini with Retina Display Review',
            },
        },
        {
            # From http://on.aol.com/video/how-to-make-a-next-level-fruit-salad-518086247
            'url': '5min:518086247',
            'md5': 'e539a9dd682c288ef5a498898009f69e',
            'info_dict': {
                'id': '518086247',
                'ext': 'mp4',
                'title': 'How to Make a Next-Level Fruit Salad',
            },
        },
    ]

    @classmethod
    def _build_result(cls, video_id):
        return cls.url_result('5min:%s' % video_id, cls.ie_key())

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        embed_url = 'https://embed.5min.com/playerseed/?playList=%s' % video_id
        embed_page = self._download_webpage(embed_url, video_id,
                                            'Downloading embed page')
        sid = self._search_regex(r'sid=(\d+)', embed_page, 'sid')
        query = compat_urllib_parse.urlencode({
            'func': 'GetResults',
            'playlist': video_id,
            'sid': sid,
            'isPlayerSeed': 'true',
            'url': embed_url,
        })
        response = self._download_json(
            'https://syn.5min.com/handlers/SenseHandler.ashx?' + query,
            video_id)
        if not response['success']:
            err_msg = response['errorMessage']
            if err_msg == 'ErrorVideoUserNotGeo':
                msg = 'Video not available from your location'
            else:
                msg = 'Aol said: %s' % err_msg
            raise ExtractorError(msg, expected=True, video_id=video_id)
        info = response['binding'][0]

        second_id = compat_str(int(video_id[:-2]) + 1)
        formats = []
        for quality, height in [(1, 320), (2, 480), (4, 720), (8, 1080)]:
            if any(r['ID'] == quality for r in info['Renditions']):
                formats.append({
                    'format_id': compat_str(quality),
                    'url': 'http://avideos.5min.com/%s/%s/%s_%s.mp4' % (second_id[-3:], second_id, video_id, quality),
                    'height': height,
                })

        return {
            'id': video_id,
            'title': info['Title'],
            'formats': formats,
        }

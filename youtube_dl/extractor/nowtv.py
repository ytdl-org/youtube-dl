# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
    unified_strdate,
    int_or_none,
)

class NowTvIE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'''(?x)
                        (?:https?://)?
                        (
                            (?:www\.)?nowtv\.de
                            /(rtl|rtl2|rtlnitro||superrtl|ntv|vox)(?P<path>/.*?)/player
                        )'''

    _TESTS = [
        {
            'url': 'http://www.nowtv.de/vox/der-hundeprofi/buero-fall-chihuahua-joel/player',
            'info_dict': {
                'id': '128953',
                'ext': 'mp4',
                'title': 'B\u00fcro-Fall \/ Chihuahua \'Joel\'',
                'description': 'md5:ce843b6b5901d9a7f7d04d1bbcdb12de',
                'upload_date': '2015-05-23 19:10:00',
                'duration': '00:51:32',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Only works from Germany',
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        info_url = 'https://api.nowtv.de/v3/movies' + mobj.group('path') + '?fields=*,format,files,breakpoints,paymentPaytypes,trailers'
        info = self._download_json(info_url, None)

        video_id = info['id']
        title = info['title']
        description = info['articleShort']
        duration = info['duration']
        upload_date = unified_strdate(info['broadcastStartDate'])
        free = info['free']
        station = info['format']['station']
        thumbnail = info['format']['defaultImage169Logo']

        if station == 'rtl':
            base_url = 'http://hls.fra.rtlnow.de/hls-vod-enc/'
        elif station == 'rtl2':
            base_url = 'http://hls.fra.rtl2now.de/hls-vod-enc/'
        elif station == 'vox':
            base_url = 'http://hls.fra.voxnow.de/hls-vod-enc/'
        elif station == 'nitro':
            base_url = 'http://hls.fra.rtlnitronow.de/hls-vod-enc/'
        elif station == 'ntv':
            base_url = 'http://hls.fra.n-tvnow.de/hls-vod-enc/'
        elif station == 'superrtl':
            base_url = 'http://hls.fra.superrtlnow.de/hls-vod-enc/'

        formats = []
        for item in info['files']['items']:
            if item['type'] != 'video/x-abr':
                continue

            fmt = {
                'url': base_url + item['path'] + '.m3u8',
                'tbr': int_or_none(item['bitrate']),
                'ext': 'mp4',
                'format_id': int_or_none(item['id']),
            }
            formats.append(fmt)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
        }

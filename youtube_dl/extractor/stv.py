# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    float_or_none,
    int_or_none,
)


class STVPlayerIE(InfoExtractor):
    IE_NAME = 'stv:player'
    _VALID_URL = r'https?://player\.stv\.tv/(?P<type>episode|video)/(?P<id>[a-z0-9]{4})'
    _TEST = {
        'url': 'https://player.stv.tv/video/4gwd/emmerdale/60-seconds-on-set-with-laura-norton/',
        'md5': '5adf9439c31d554f8be0707c7abe7e0a',
        'info_dict': {
            'id': '5333973339001',
            'ext': 'mp4',
            'upload_date': '20170301',
            'title': '60 seconds on set with Laura Norton',
            'description': "How many questions can Laura - a.k.a Kerry Wyatt - answer in 60 seconds? Let\'s find out!",
            'timestamp': 1488388054,
            'uploader_id': '1486976045',
        },
        'skip': 'this resource is unavailable outside of the UK',
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1486976045/default_default/index.html?videoId=%s'
    _PTYPE_MAP = {
        'episode': 'episodes',
        'video': 'shortform',
    }

    def _real_extract(self, url):
        ptype, video_id = re.match(self._VALID_URL, url).groups()
        resp = self._download_json(
            'https://player.api.stv.tv/v1/%s/%s' % (self._PTYPE_MAP[ptype], video_id),
            video_id)

        result = resp['results']
        video = result['video']
        video_id = compat_str(video['id'])

        subtitles = {}
        _subtitles = result.get('_subtitles') or {}
        for ext, sub_url in _subtitles.items():
            subtitles.setdefault('en', []).append({
                'ext': 'vtt' if ext == 'webvtt' else ext,
                'url': sub_url,
            })

        programme = result.get('programme') or {}

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': self.BRIGHTCOVE_URL_TEMPLATE % video_id,
            'description': result.get('summary'),
            'duration': float_or_none(video.get('length'), 1000),
            'subtitles': subtitles,
            'view_count': int_or_none(result.get('views')),
            'series': programme.get('name') or programme.get('shortName'),
            'ie_key': 'BrightcoveNew',
        }

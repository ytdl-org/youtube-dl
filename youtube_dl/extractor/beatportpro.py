# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re
import json


class BeatportProIE(InfoExtractor):
    _VALID_URL = r'https?://pro\.beatport\.com/track/.*/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://pro.beatport.com/track/synesthesia-original-mix/5379371',
        'md5': 'b3c34d8639a2f6a7f734382358478887',
        'info_dict': {
            'id': 5379371,
            'display-id': 'synesthesia-original-mix',
            'ext': 'mp4',
            'title': 'Froxic - Synesthesia (Original Mix)',
        },
    }, {
        'url': 'https://pro.beatport.com/track/love-and-war-original-mix/3756896',
        'md5': 'e44c3025dfa38c6577fbaeb43da43514',
        'info_dict': {
            'id': 3756896,
            'display-id': 'love-and-war-original-mix',
            'ext': 'mp3',
            'title': 'Wolfgang Gartner - Love & War (Original Mix)',
        },
    }, {
        'url': 'https://pro.beatport.com/track/birds-original-mix/4991738',
        'md5': 'a1fd8e8046de3950fd039304c186c05f',
        'info_dict': {
            'id': 4991738,
            'display-id': 'birds-original-mix',
            'ext': 'mp4',
            'title': "Tos, Middle Milk, Mumblin' Johnsson - Birds (Original Mix)",
        }
    }]

    def _real_extract(self, url):
        track_id = self._match_id(url)
        webpage = self._download_webpage(url, track_id)

        # Extract "Playables" JSON information from the page
        playables = self._search_regex(r'window\.Playables = ({.*?});', webpage,
                                       'playables info', flags=re.DOTALL)
        playables = json.loads(playables)

        # Find first track with matching ID (always the first one listed?)
        track = next(filter(lambda t: t['id'] == int(track_id), playables['tracks']))

        # Construct title from artist(s), track name, and mix name
        title = ', '.join((a['name'] for a in track['artists'])) + ' - ' + track['name']
        if track['mix']:
            title += ' (' + track['mix'] + ')'

        # Get format information
        formats = []
        for ext, info in track['preview'].items():
            if info['url'] is None:
                continue
            fmt = {
                'url': info['url'],
                'ext': ext,
                'format_id': ext,
                'vcodec': 'none',
            }
            if ext == 'mp3':
                fmt['preference'] = 0
                fmt['acodec'] = 'mp3'
                fmt['abr'] = 96
                fmt['asr'] = 44100
            elif ext == 'mp4':
                fmt['preference'] = 1
                fmt['acodec'] = 'aac'
                fmt['abr'] = 96
                fmt['asr'] = 44100
            formats += [fmt]
        formats.sort(key=lambda f: f['preference'])

        # Get album art as thumbnails
        imgs = []
        for name, info in track['images'].items():
            if name == 'dynamic' or info['url'] is None:
                continue
            img = {
                'id': name,
                'url': info['url'],
                'height': info['height'],
                'width': info['width'],
            }
            imgs += [img]

        return {
            'id': track['id'],
            'display-id': track['slug'],
            'title': title,
            'formats': formats,
            'thumbnails': imgs,
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (int_or_none, try_get)


class HarvardDceIE(InfoExtractor):
    _VALID_URL = r'https?://matterhorn\.dce\.harvard\.edu/engage/player/watch.html\?id=(?P<id>[0-9a-z-]+)'
    _TEST = {
        'url': 'https://matterhorn.dce.harvard.edu/engage/player/watch.html?id=1a5e78df-fbb5-4c97-be82-860fb69b4379',
        'info_dict': {
            'id': '1a5e78df-fbb5-4c97-be82-860fb69b4379',
            'title': 'Lecture 4',
            'ext': 'mp4',
            'description': 'Review, Kernels, Normality',
            'duration': float(3187),
        }
    }

    def _real_extract(self, url):
        vid = self._match_id(url)
        json_url = 'https://matterhorn.dce.harvard.edu/search/episode.json'
        response = self._download_json(json_url, vid, query={'id': vid})
        result = response['search-results']['result']

        formats = result['mediapackage']['media']['track']

        def sort_format(track):
            return try_get(track, lambda x: x['video']['bitrate']) or 0
        formats.sort(key=sort_format)

        def map_format(track):
            audio = track.get('audio') or {}
            video = track.get('video') or {}
            return {
                'url': track['url'],

                'acodec': try_get(audio, lambda x: x['encoder']['type']),
                'abr': audio.get('bitrate'),

                'vcodec': try_get(video, lambda x: x['encoder']['type']),
                'vbr': video.get('bitrate'),
                'fps': video.get('framerate'),
                'resolution': video.get('resolution'),
            }
        formats = map(map_format, formats)

        duration = result['mediapackage'].get('duration')
        duration = int_or_none(duration, scale=1000)

        return {
            'id': vid,
            'title': result.get('dcTitle'),
            'formats': formats,
            'description': result.get('dcDescription'),
            'duration': duration,
            'license': result.get('dcLicense'),
        }

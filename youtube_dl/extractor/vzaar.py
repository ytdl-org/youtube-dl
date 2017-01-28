# coding: utf-8
from __future__ import unicode_literals

from ..utils import float_or_none, int_or_none
from .common import InfoExtractor


class VzaarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|view)\.)?vzaar\.com/(?:videos/)?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://vzaar.com/videos/1152805',
        'md5': 'bde5ddfeb104a6c56a93a06b04901dbf',
        'info_dict': {
            'id': '1152805',
            'ext': 'mp4',
            'title': 'sample video (public)',
        },
    }, {
        'url': 'https://view.vzaar.com/27272/player',
        'md5': '3b50012ac9bbce7f445550d54e0508f2',
        'info_dict': {
            'id': '27272',
            'ext': 'mp3',
            'title': 'MP3',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://view.vzaar.com/v2/%s/video' % video_id, video_id)
        source_url = video_data['sourceUrl']

        info = {
            'id': video_id,
            'title': video_data['videoTitle'],
            'url': source_url,
            'thumbnail': self._proto_relative_url(video_data.get('poster')),
            'duration': float_or_none(video_data.get('videoDuration')),
        }
        if 'audio' in source_url:
            info.update({
                'vcodec': 'none',
                'ext': 'mp3',
            })
        else:
            info.update({
                'width': int_or_none(video_data.get('width')),
                'height': int_or_none(video_data.get('height')),
                'ext': 'mp4',
            })
        return info

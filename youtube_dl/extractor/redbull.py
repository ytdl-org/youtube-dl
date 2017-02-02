# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor


class RedBullIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull\.tv/video/(?P<id>AP-\w+)'
    _TEST = {
        'url': 'https://www.redbull.tv/video/AP-1Q756YYX51W11/abc-of-wrc',
        'md5': '78e860f631d7a846e712fab8c5fe2c38',
        'info_dict': {
            'id': 'AP-1Q756YYX51W11',
            'ext': 'mp4',
            'title': 'ABC of...WRC',
            'description': 'Buckle up for a crash course in the terminology, rules, drivers, and courses of the World Rally Championship.'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        access_token = self._download_json(
            'http://api-v2.redbull.tv/start?build=4.0.9&category=smartphone&os_version=23&os_family=android',
            video_id, note='Downloading  access token',
        )['auth']['access_token']

        info = self._download_json(
            'https://api-v2.redbull.tv/views/%s' % video_id,
            video_id, note='Downloading video information',
            headers={'Authorization': 'Bearer ' + access_token}
        )['blocks'][0]['top'][0]

        m3u8_url = info['video_product']['url']
        title = info['title']

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': info.get('short_description'),
            'genre': info.get('genre'),
            'duration': info.get('duration')
        }

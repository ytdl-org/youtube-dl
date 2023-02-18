# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KickIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kick\.com/video/(?P<id>[0-9a-zA-Z-]+)'
    _TEST = {
        'url': 'https://kick.com/video/82a3c11d-7a17-4747-aecb-2e61413eb11f',
        'md5': 'f052bc1046cd9ca6751925dd12420010',
        'info_dict': {
            'id': '82a3c11d-7a17-4747-aecb-2e61413eb11f',
            'ext': 'm3u8',
            'title': 'Weekly Stake Stream',
            'uploader': 'Eddie',
            'thumbnail': r're:^https?://.*\.jpg.*$',
        }
    }

    def _real_extract(self, url):
        id = self._match_id(url)

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla',
        }

        data = self._download_json('https://kick.com/api/v1/video/%s' % id, id, headers=headers)

        video_url = data['source']
        formats = self._extract_m3u8_formats(
            data['source'], id, 'mp4')
        self._sort_formats(formats)
        title = data['livestream']['session_title']
        uploader = data['livestream']['channel']['user']['username']
        thumbnail = data['livestream']['thumbnail']

        return {
            'url': video_url,
            'id': id,
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'formats': formats,
        }

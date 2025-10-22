# coding: utf-8
from __future__ import unicode_literals

import json
import posixpath

from .common import InfoExtractor
from ..utils import urljoin


class NinjaStreamIE(InfoExtractor):
    """
    Handles downloading video from ninjastream.to
    """
    _VALID_URL = r'https?://(?:www\.)?ninjastream\.to/(?:download|watch)/(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'https://ninjastream.to/watch/GbJQP8rawQ7rw',
            'info_dict': {
                'id': 'GbJQP8rawQ7rw',
                'ext': 'mp4',
                'title': 'Big Buck Bunny 360 10s 5MB'
            },
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Get the hosted webpage
        webpage = self._download_webpage(url, video_id)

        # The v-bind:file will give us the correct title for the video
        file_meta = self._parse_json(
            self._html_search_regex(r'v-bind:file="([^"]*)"', webpage,
                                    video_id),
            video_id, fatal=False) or {}

        try:
            filename = posixpath.splitext(file_meta['name'])[0]
        except KeyError:
            filename = 'ninjastream.to'

        thumbnail = file_meta.get('poster_id')
        if thumbnail:
            thumbnail = urljoin('https://cdn.ninjastream.to/', thumbnail)

        data = {'id': video_id}
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Referer': url,
        }
        data = json.dumps(data, separators=(',', ':')).encode('utf-8')
        stream_meta = self._download_json('https://ninjastream.to/api/video/get',
                                          video_id, data=data, headers=headers)

        # Get and parse the m3u8 information
        stream_url = stream_meta['result']['playlist']
        formats = self._extract_m3u8_formats(
            stream_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        return {
            'formats': formats,
            'id': video_id,
            'thumbnail': thumbnail,
            'title': filename,
        }

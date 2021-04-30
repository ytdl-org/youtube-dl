# coding: utf-8
from __future__ import unicode_literals

import os

from .common import InfoExtractor
from ..utils import ExtractorError


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

        # The links to the m3u8 file will be buried and html encoded in
        # the <file-watch-jwplayer> tag
        jwplayer_link = self._html_search_regex(
            r'<file-watch-jwplayer (.*)', webpage,
            'file-watch-jwplayer', fatal=False)

        if jwplayer_link is None:
            raise ExtractorError(
                'NinjaStream: Failed to find the file information on the website')

        # The v-bind:file will give us the correct title for the video
        file_meta = self._parse_json(
            self._search_regex(r'v-bind:file=\"(\{.*?\})\"', jwplayer_link,
                               video_id),
            video_id, fatal=False)

        filename = video_id
        if file_meta is not None:
            filename = os.path.splitext(file_meta.get('name'))[0]

        # The v-bind:stream will give us the location of the m3u8 file
        stream_meta = self._parse_json(
            self._search_regex(r'v-bind:stream=\"(\{.*?\})\"',
                               jwplayer_link, video_id),
            video_id, fatal=False)

        if stream_meta is None:
            raise ExtractorError(
                'NinjaStream: Failed to find the m3u8 information on website')

        url = '{0}/{1}/index.m3u8'.format(stream_meta['host'],
                                          stream_meta['hash'])

        # Get and parse the m3u8 information
        formats = self._extract_m3u8_formats(
            url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls', fatal=False)

        return {
            'formats': formats,
            'id': video_id,
            'title': filename,
        }

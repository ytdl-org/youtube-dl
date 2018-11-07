# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CloudflareStreamIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:watch\.)?cloudflarestream\.com/|
                            embed\.cloudflarestream\.com/embed/[^/]+\.js\?.*?\bvideo=
                        )
                        (?P<id>[\da-f]+)
                    '''
    _TESTS = [{
        'url': 'https://embed.cloudflarestream.com/embed/we4g.fla9.latest.js?video=31c9291ab41fac05471db4e73aa11717',
        'info_dict': {
            'id': '31c9291ab41fac05471db4e73aa11717',
            'ext': 'mp4',
            'title': '31c9291ab41fac05471db4e73aa11717',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://watch.cloudflarestream.com/9df17203414fd1db3e3ed74abbe936c1',
        'only_matching': True,
    }, {
        'url': 'https://cloudflarestream.com/31c9291ab41fac05471db4e73aa11717/manifest/video.mpd',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [
            mobj.group('url')
            for mobj in re.finditer(
                r'<script[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//embed\.cloudflarestream\.com/embed/[^/]+\.js\?.*?\bvideo=[\da-f]+?.*?)\1',
                webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = self._extract_m3u8_formats(
            'https://cloudflarestream.com/%s/manifest/video.m3u8' % video_id,
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls',
            fatal=False)
        formats.extend(self._extract_mpd_formats(
            'https://cloudflarestream.com/%s/manifest/video.mpd' % video_id,
            video_id, mpd_id='dash', fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }

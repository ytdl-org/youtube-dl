# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    decode_packed_codes,
    determine_ext,
    ExtractorError,
    urlencode_postdata,
)


class DarkiboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?darkibox\.com/(?:embed-|d/)?(?P<id>[a-z0-9]+)(?:\.html)?'
    IE_NAME = 'darkibox'
    _TESTS = [{
        'url': 'https://darkibox.com/embed-vku4mg7gc7wp.html',
        'only_matching': True,
    }, {
        'url': 'https://darkibox.com/vku4mg7gc7wp',
        'only_matching': True,
    }, {
        'url': 'https://darkibox.com/d/vku4mg7gc7wp',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        embed_url = 'https://darkibox.com/embed-%s.html' % video_id
        webpage = self._download_webpage(embed_url, video_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=None)
        if title:
            title = re.sub(r'\s*-\s*Darkibox\s*$', '', title, flags=re.IGNORECASE).strip()
        if not title:
            title = video_id

        # POST to /dl endpoint to get the player page
        webpage = self._download_webpage(
            'https://darkibox.com/dl', video_id,
            note='Downloading player page',
            data=urlencode_postdata({
                'op': 'embed',
                'file_code': video_id,
                'auto': '1',
            }),
            headers={
                'Referer': embed_url,
                'Content-type': 'application/x-www-form-urlencoded',
                'Origin': 'https://darkibox.com',
            })

        # Unpack eval(function(p,a,c,k,e,d){...}) if present
        packed = self._search_regex(
            r'(?s)(eval\(function\(p,a,c,k,e,d\)\{.+?\)\))',
            webpage, 'packed code', default=None)
        if packed:
            webpage = decode_packed_codes(packed)

        # Extract video URL from PlayerJS file:"URL" or sources
        # Try file:"url" (PlayerJS format)
        video_url = self._search_regex(
            r'file\s*:\s*"([^"]+)"', webpage, 'video url', default=None)

        if not video_url:
            # Try [label]url format (multi-quality)
            video_url = self._search_regex(
                r'file\s*:\s*"(\[[^"]+\])"', webpage, 'video url list', default=None)

        if not video_url:
            # Try src: or source
            video_url = self._search_regex(
                r'(?:src|source)\s*[:=]\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)',
                webpage, 'video url', default=None)

        if not video_url:
            raise ExtractorError('Unable to extract video URL', expected=True)

        # Handle [label]url multi-quality format
        # e.g. [720p]https://...,[480p]https://...
        if video_url.startswith('['):
            formats = []
            for m in re.finditer(r'\[([^\]]+)\]([^,\s"]+)', video_url):
                label, fmt_url = m.groups()
                height = self._search_regex(
                    r'(\d+)', label, 'height', default=None)
                formats.append({
                    'url': fmt_url,
                    'format_id': label,
                    'height': int(height) if height else None,
                })
            if not formats:
                raise ExtractorError('Unable to parse multi-quality URLs', expected=True)
        elif determine_ext(video_url) == 'm3u8':
            formats = self._extract_m3u8_formats(
                video_url, video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='hls',
                fatal=False)
        else:
            formats = [{
                'url': video_url,
                'format_id': 'sd',
            }]

        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r'image\s*:\s*"([^"]+)"', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'http_headers': {'Referer': embed_url},
        }

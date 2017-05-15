from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class ChaturbateIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?chaturbate\.com/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.chaturbate.com/siswet19/',
        'info_dict': {
            'id': 'siswet19',
            'ext': 'mp4',
            'title': 're:^siswet19 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Room is offline',
    }, {
        'url': 'https://en.chaturbate.com/siswet19/',
        'only_matching': True,
    }]

    _ROOM_OFFLINE = 'Room is currently offline'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        m3u8_urls = []

        for m in re.finditer(
                r'(["\'])(?P<url>http.+?\.m3u8.*?)\1', webpage):
            m3u8_fast_url, m3u8_no_fast_url = m.group('url'), m.group(
                'url').replace('_fast', '')
            for m3u8_url in (m3u8_fast_url, m3u8_no_fast_url):
                if m3u8_url not in m3u8_urls:
                    m3u8_urls.append(m3u8_url)

        if not m3u8_urls:
            error = self._search_regex(
                [r'<span[^>]+class=(["\'])desc_span\1[^>]*>(?P<error>[^<]+)</span>',
                 r'<div[^>]+id=(["\'])defchat\1[^>]*>\s*<p><strong>(?P<error>[^<]+)<'],
                webpage, 'error', group='error', default=None)
            if not error:
                if any(p in webpage for p in (
                        self._ROOM_OFFLINE, 'offline_tipping', 'tip_offline')):
                    error = self._ROOM_OFFLINE
            if error:
                raise ExtractorError(error, expected=True)
            raise ExtractorError('Unable to find stream URL')

        formats = []
        for m3u8_url in m3u8_urls:
            m3u8_id = 'fast' if '_fast' in m3u8_url else 'slow'
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, ext='mp4',
                # ffmpeg skips segments for fast m3u8
                preference=-10 if m3u8_id == 'fast' else None,
                m3u8_id=m3u8_id, fatal=False, live=True))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'thumbnail': 'https://roomimg.stream.highwebmedia.com/ri/%s.jpg' % video_id,
            'age_limit': self._rta_search(webpage),
            'is_live': True,
            'formats': formats,
        }

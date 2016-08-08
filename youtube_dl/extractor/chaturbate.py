from __future__ import unicode_literals

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

        m3u8_url = self._search_regex(
            r'src=(["\'])(?P<url>http.+?\.m3u8.*?)\1', webpage,
            'playlist', default=None, group='url')

        if not m3u8_url:
            error = self._search_regex(
                [r'<span[^>]+class=(["\'])desc_span\1[^>]*>(?P<error>[^<]+)</span>',
                 r'<div[^>]+id=(["\'])defchat\1[^>]*>\s*<p><strong>(?P<error>[^<]+)<'],
                webpage, 'error', group='error', default=None)
            if not error:
                if any(p not in webpage for p in (
                        self._ROOM_OFFLINE, 'offline_tipping', 'tip_offline')):
                    error = self._ROOM_OFFLINE
            if error:
                raise ExtractorError(error, expected=True)
            raise ExtractorError('Unable to find stream URL')

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'thumbnail': 'https://cdn-s.highwebmedia.com/uHK3McUtGCG3SMFcd4ZJsRv8/roomimage/%s.jpg' % video_id,
            'age_limit': self._rta_search(webpage),
            'is_live': True,
            'formats': formats,
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)
from ..compat import compat_urlparse


class UKDevilzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ukdevilz\.com/watch/(-)?(?P<id>[\d]*_[\d]*)'
    IE_DESC = 'UKDEVILZ'
    _TEST = {
        'url': 'https://ukdevilz.com/watch/-160418850_456239050',
        'md5': 'fe608143263af08b0160932561ed1a8a',
        'info_dict': {
            'id': '160418850_456239050',
            'ext': 'mp4',
            'title': 'Twix hot beverage',
            'description': 'md5:7c941f7c8ae9c83d06a6cea1722ae859',
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        iframe_url = self._search_regex(r'<iframe[^>]+src=(["\'])(?P<iFrameUrl>(?:https?:)?//ukdevilz\.com/player/[^"\']+)', webpage, 'iFrameUrl', group='iFrameUrl')
        iframe = self._download_webpage(iframe_url, video_id)

        playlist_url = compat_urlparse.urljoin(url, self._search_regex(r'window.playlistUrl\s*=\s*["\'](?P<playlistUrl>[^"\']+)', iframe, 'playlistUrl'))
        playlist = self._download_json(playlist_url, video_id)

        # playlist has no info about the width and file extension of the HLS stream
        # the HLS stream seems to always be the highest quality of the other streams, so just use that
        max_width = 0
        ext = ''
        for source in playlist.get('sources'):
            if source.get('label') and int(source.get('label')) > max_width:
                max_width = int_or_none(source.get('label'))
                ext = source.get('type')

        formats = []
        for source in playlist.get('sources'):
            formats.append({
                'url': source.get('file') if not source.get('file').startswith('/') else compat_urlparse.urljoin(url, source.get('file')),
                'ext': ext if source.get('type') == 'hls' else source.get('type'),
                'protocol': 'm3u8' if source.get('type') == 'hls' else compat_urlparse.urlparse(source.get('file')).scheme,
                'width': int_or_none(source.get('label') or max_width)
            })
        self._sort_formats(formats)

        description = (self._search_regex(r'(?s)<div[^>]+\bclass=["\']description["\'][^>]*>(.+?)</div>', webpage, 'description', default='', fatal=False)
                       or self._og_search_description(webpage))

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': description,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'tags': self._html_search_meta('keywords', webpage)
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
)


class InfomaniakVod2IE(InfoExtractor):
    IE_NAME = 'infomaniak:vod2'
    _VALID_URL = r'https?://player\.vod2\.infomaniak\.com/embed/(?P<id>[0-9a-z]+)'
    _TEST = {
        'url': 'https://player.vod2.infomaniak.com/embed/1jhvl2uqg6ywp',
        'info_dict': {
            'id': '1jhvl2uqg6xis',
            'display_id': '1jhvl2uqg6ywp',
            'ext': 'mp4',
            'title': 'Conférence à Dyo, octobre 2022',
            'thumbnail': r're:^https?://.*\.(?:jpe?g|png)$',
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        share_id = self._match_id(url)
        share = self._download_json(
            'https://api.infomaniak.com/2/vod/res/shares/%s.json' % share_id,
            share_id)
        data = (share or {}).get('data') or {}
        media = data.get('media') or []

        entries = []
        for m in media:
            if not isinstance(m, dict):
                continue
            media_id = m.get('id') or share_id
            title = m.get('title') or share_id
            duration = parse_duration(m.get('duration'))
            thumbnails = m.get('thumbnails') or {}
            thumbnail = thumbnails.get('poster') or thumbnails.get('image')

            source = m.get('source') or {}
            formats = []

            hls_url = source.get('hls')
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, media_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))

            mpd_url = source.get('dash')
            if mpd_url:
                formats.extend(self._extract_mpd_formats(
                    mpd_url, media_id, mpd_id='dash', fatal=False))

            best_url = source.get('best')
            if best_url:
                formats.append({
                    'url': best_url,
                    'format_id': 'http',
                })

            self._sort_formats(formats)

            entries.append({
                'id': media_id,
                'display_id': share_id,
                'title': title,
                'duration': duration,
                'thumbnail': thumbnail,
                'formats': formats,
                'webpage_url': url,
            })

        if not entries:
            # Keep the error message actionable for site support requests
            raise ExtractorError('Unable to find any media in share JSON', expected=True)

        if len(entries) == 1:
            return entries[0]

        return self.playlist_result(entries, playlist_id=share_id)



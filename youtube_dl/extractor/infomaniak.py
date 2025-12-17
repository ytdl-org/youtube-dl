# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str as str
from ..utils import (
    ExtractorError,
    merge_dicts,
    parse_duration,
    str_or_none,
    T,
    traverse_obj,
    url_or_none,
)


class InfomaniakVod2IE(InfoExtractor):
    IE_NAME = 'infomaniak:vod2'
    _VALID_URL = r'https?://player\.vod2\.infomaniak\.com/embed/(?P<id>[0-9a-z]+)'
    _TEST = {
        'url': 'https://player.vod2.infomaniak.com/embed/1jhvl2uqg6ywp',
        'md5': '08c3a89906b70a614fa0fdb057e8a22e',
        'info_dict': {
            'id': '1jhvl2uqg6xis',
            'display_id': '1jhvl2uqg6ywp',
            'ext': 'mp4',
            'title': 'Conférence à Dyo, octobre 2022',
            'thumbnail': r're:https?://.+\.(?:jpe?g|png)$',
        },
    }

    def _real_extract(self, url):
        share_id = self._match_id(url)
        share = self._download_json(
            'https://api.infomaniak.com/2/vod/res/shares/%s.json' % share_id,
            share_id)
        entries = []
        for media in traverse_obj(share, (
                'data', 'media', lambda _, v: v.get('source').get)):
            media_id = media.get('id') or share_id
            source = media['source']
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
                    'preference': 10,
                })

            self._sort_formats(formats)

            entries.append(merge_dicts(
                traverse_obj(media, {
                    'id': ('id', T(str_or_none)),
                    'title': ('title', T(str)),
                    'duration': ('duration', T(parse_duration)),
                    'thumbnail': ('thumbnails', ('poster', 'image'), T(url_or_none), any),
                }), {
                    'formats': formats,
                }))

        if len(entries) == 1:
            return merge_dicts({
                'id': share_id,
                'display_id': share_id,
            }, entries[0], rev=True)

        entries = [e for e in entries if e.get('id')]
        if not entries:
            # Keep the error message actionable for site support requests
            raise ExtractorError('Unable to find any media in share JSON', expected=True)

        return self.playlist_result(entries, playlist_id=share_id)



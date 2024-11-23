# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    merge_dicts,
    T,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class ClipchampIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?clipchamp\.com/watch/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://clipchamp.com/watch/gRXZ4ZhdDaU',
        'info_dict': {
            'id': 'gRXZ4ZhdDaU',
            'ext': 'mp4',
            'title': 'Untitled video',
            'uploader': 'Alexander Schwartz',
            'timestamp': 1680805580,
            'upload_date': '20230406',
            'thumbnail': r're:^https?://.+\.jpg',
        },
        'params': {
            'skip_download': 'm3u8',
            'format': 'bestvideo',
        },
    }]

    _STREAM_URL_TMPL = 'https://%s.cloudflarestream.com/%s/manifest/video.%s'
    _STREAM_URL_QUERY = {'parentOrigin': 'https://clipchamp.com'}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data = self._search_nextjs_data(webpage, video_id)['props']['pageProps']['video']

        storage_location = data.get('storage_location')
        if storage_location != 'cf_stream':
            raise ExtractorError('Unsupported clip storage location "%s"' % (storage_location,))

        path = data['download_url']
        iframe = self._download_webpage(
            'https://iframe.cloudflarestream.com/' + path, video_id, 'Downloading player iframe')
        subdomain = self._search_regex(
            r'''\bcustomer-domain-prefix\s*=\s*("|')(?P<sd>[\w-]+)\1''', iframe,
            'subdomain', group='sd', fatal=False) or 'customer-2ut9yn3y6fta1yxe'

        formats = self._extract_mpd_formats(
            self._STREAM_URL_TMPL % (subdomain, path, 'mpd'), video_id,
            query=self._STREAM_URL_QUERY, fatal=False, mpd_id='dash')
        formats.extend(self._extract_m3u8_formats(
            self._STREAM_URL_TMPL % (subdomain, path, 'm3u8'), video_id, 'mp4',
            query=self._STREAM_URL_QUERY, fatal=False, m3u8_id='hls'))

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'uploader': ' '.join(traverse_obj(data, ('creator', ('first_name', 'last_name'), T(compat_str)))) or None,
        }, traverse_obj(data, {
            'title': ('project', 'project_name', T(compat_str)),
            'timestamp': ('created_at', T(unified_timestamp)),
            'thumbnail': ('thumbnail_url', T(url_or_none)),
        }), rev=True)

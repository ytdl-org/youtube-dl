from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    str_to_int,
)


class ZippCastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?zippcast\.com/(?:video/|videoview\.php\?.*\bvplay=)(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        # m3u8, hq direct link
        'url': 'http://www.zippcast.com/video/c9cfd5c7e44dbc29c81',
        'md5': '5ea0263b5606866c4d6cda0fc5e8c6b6',
        'info_dict': {
            'id': 'c9cfd5c7e44dbc29c81',
            'ext': 'mp4',
            'title': '[Vinesauce] Vinny - Digital Space Traveler',
            'description': 'Muted on youtube, but now uploaded in it\'s original form.',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'vinesauce',
            'view_count': int,
            'categories': ['Entertainment'],
            'tags': list,
        },
    }, {
        # f4m, lq ipod direct link
        'url': 'http://www.zippcast.com/video/b79c0a233e9c6581775',
        'only_matching': True,
    }, {
        'url': 'http://www.zippcast.com/videoview.php?vplay=c9cfd5c7e44dbc29c81&auto=no',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.zippcast.com/video/%s' % video_id, video_id)

        formats = []
        video_url = self._search_regex(
            r'<source[^>]+src=(["\'])(?P<url>.+?)\1', webpage,
            'video url', default=None, group='url')
        if video_url:
            formats.append({
                'url': video_url,
                'format_id': 'http',
                'preference': 0,  # direct link is almost always of worse quality
            })
        src_url = self._search_regex(
            r'src\s*:\s*(?:escape\()?(["\'])(?P<url>http://.+?)\1',
            webpage, 'src', default=None, group='url')
        ext = determine_ext(src_url)
        if ext == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                src_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False))
        elif ext == 'f4m':
            formats.extend(self._extract_f4m_formats(
                src_url, video_id, f4m_id='hds', fatal=False))
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage) or self._html_search_meta(
            'description', webpage)
        uploader = self._search_regex(
            r'<a[^>]+href="https?://[^/]+/profile/[^>]+>([^<]+)</a>',
            webpage, 'uploader', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        view_count = str_to_int(self._search_regex(
            r'>([\d,.]+) views!', webpage, 'view count', fatal=False))

        categories = re.findall(
            r'<a[^>]+href="https?://[^/]+/categories/[^"]+">([^<]+),?<',
            webpage)
        tags = re.findall(
            r'<a[^>]+href="https?://[^/]+/search/tags/[^"]+">([^<]+),?<',
            webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'view_count': view_count,
            'categories': categories,
            'tags': tags,
            'formats': formats,
        }

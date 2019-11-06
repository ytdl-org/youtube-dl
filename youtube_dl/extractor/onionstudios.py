# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    int_or_none,
    js_to_json,
    parse_iso8601,
    try_get,
)


class OnionStudiosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onionstudios\.com/(?:video(?:s/[^/]+-|/)|embed\?.*\bid=)(?P<id>\d+)(?!-)'

    _TESTS = [{
        'url': 'http://www.onionstudios.com/videos/hannibal-charges-forward-stops-for-a-cocktail-2937',
        'md5': '5a118d466d62b5cd03647cf2c593977f',
        'info_dict': {
            'id': '2937',
            'ext': 'mp4',
            'title': 'Hannibal charges forward, stops for a cocktail',
            'description': 'md5:545299bda6abf87e5ec666548c6a9448',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'a.v. club',
            'upload_date': '20150619',
            'timestamp': 1434728546,
        },
    }, {
        'url': 'http://www.onionstudios.com/embed?id=2855&autoplay=true',
        'only_matching': True,
    }, {
        'url': 'http://www.onionstudios.com/video/6139.json',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'(?s)<(?:iframe|bulbs-video)[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?onionstudios\.com/(?:embed.+?|video/\d+\.json))\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://onionstudios.com/embed/dc94dc2899fe644c0e7241fa04c1b732.js',
            video_id)
        mcp_id = compat_str(self._parse_json(self._search_regex(
            r'window\.mcpMapping\s*=\s*({.+?});', webpage,
            'MCP Mapping'), video_id, js_to_json)[video_id]['mcp_id'])
        video_data = self._download_json(
            'https://api.vmh.univision.com/metadata/v1/content/' + mcp_id,
            mcp_id)['videoMetadata']
        iptc = video_data['photoVideoMetadataIPTC']
        title = iptc['title']['en']
        fmg = video_data.get('photoVideoMetadata_fmg') or {}
        tvss_domain = fmg.get('tvssDomain') or 'https://auth.univision.com'
        data = self._download_json(
            tvss_domain + '/api/v3/video-auth/url-signature-tokens',
            mcp_id, query={'mcpids': mcp_id})['data'][0]
        formats = []

        rendition_url = data.get('renditionUrl')
        if rendition_url:
            formats = self._extract_m3u8_formats(
                rendition_url, mcp_id, 'mp4',
                'm3u8_native', m3u8_id='hls', fatal=False)

        fallback_rendition_url = data.get('fallbackRenditionUrl')
        if fallback_rendition_url:
            formats.append({
                'format_id': 'fallback',
                'tbr': int_or_none(self._search_regex(
                    r'_(\d+)\.mp4', fallback_rendition_url,
                    'bitrate', default=None)),
                'url': fallback_rendition_url,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': try_get(iptc, lambda x: x['cloudinaryLink']['link'], compat_str),
            'uploader': fmg.get('network'),
            'duration': int_or_none(iptc.get('fileDuration')),
            'formats': formats,
            'description': try_get(iptc, lambda x: x['description']['en'], compat_str),
            'timestamp': parse_iso8601(iptc.get('dateReleased')),
        }

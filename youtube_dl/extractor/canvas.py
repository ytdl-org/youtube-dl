from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    strip_or_none,
)


class CanvasIE(InfoExtractor):
    _VALID_URL = r'https?://mediazone\.vrt\.be/api/v1/(?P<site_id>canvas|een|ketnet)/assets/(?P<id>m[dz]-ast-[^/?#&]+)'
    _TESTS = [{
        'url': 'https://mediazone.vrt.be/api/v1/ketnet/assets/md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
        'md5': '90139b746a0a9bd7bb631283f6e2a64e',
        'info_dict': {
            'id': 'md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
            'display_id': 'md-ast-4ac54990-ce66-4d00-a8ca-9eac86f4c475',
            'ext': 'flv',
            'title': 'Nachtwacht: De Greystook',
            'description': 'md5:1db3f5dc4c7109c821261e7512975be7',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1468.03,
        },
        'expected_warnings': ['is not a supported codec', 'Unknown MIME type'],
    }, {
        'url': 'https://mediazone.vrt.be/api/v1/canvas/assets/mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, video_id = mobj.group('site_id'), mobj.group('id')

        data = self._download_json(
            'https://mediazone.vrt.be/api/v1/%s/assets/%s'
            % (site_id, video_id), video_id)

        title = data['title']
        description = data.get('description')

        formats = []
        for target in data['targetUrls']:
            format_url, format_type = target.get('url'), target.get('type')
            if not format_url or not format_type:
                continue
            if format_type == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=format_type, fatal=False))
            elif format_type == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_type, fatal=False))
            elif format_type == 'MPEG_DASH':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id=format_type, fatal=False))
            elif format_type == 'HSS':
                formats.extend(self._extract_ism_formats(
                    format_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'format_id': format_type,
                    'url': format_url,
                })
        self._sort_formats(formats)

        subtitles = {}
        subtitle_urls = data.get('subtitleUrls')
        if isinstance(subtitle_urls, list):
            for subtitle in subtitle_urls:
                subtitle_url = subtitle.get('url')
                if subtitle_url and subtitle.get('type') == 'CLOSED':
                    subtitles.setdefault('nl', []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'duration': float_or_none(data.get('duration'), 1000),
            'thumbnail': data.get('posterImageUrl'),
            'subtitles': subtitles,
        }


class CanvasEenIE(InfoExtractor):
    IE_DESC = 'canvas.be and een.be'
    _VALID_URL = r'https?://(?:www\.)?(?P<site_id>canvas|een)\.be/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.canvas.be/video/de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
        'md5': 'ed66976748d12350b118455979cca293',
        'info_dict': {
            'id': 'mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
            'display_id': 'de-afspraak-veilt-voor-de-warmste-week',
            'ext': 'flv',
            'title': 'De afspraak veilt voor de Warmste Week',
            'description': 'md5:24cb860c320dc2be7358e0e5aa317ba6',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 49.02,
        },
        'expected_warnings': ['is not a supported codec'],
    }, {
        # with subtitles
        'url': 'http://www.canvas.be/video/panorama/2016/pieter-0167',
        'info_dict': {
            'id': 'mz-ast-5240ff21-2d30-4101-bba6-92b5ec67c625',
            'display_id': 'pieter-0167',
            'ext': 'mp4',
            'title': 'Pieter 0167',
            'description': 'md5:943cd30f48a5d29ba02c3a104dc4ec4e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2553.08,
            'subtitles': {
                'nl': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Pagina niet gevonden',
    }, {
        'url': 'https://www.een.be/sorry-voor-alles/herbekijk-sorry-voor-alles',
        'info_dict': {
            'id': 'mz-ast-11a587f8-b921-4266-82e2-0bce3e80d07f',
            'display_id': 'herbekijk-sorry-voor-alles',
            'ext': 'mp4',
            'title': 'Herbekijk Sorry voor alles',
            'description': 'md5:8bb2805df8164e5eb95d6a7a29dc0dd3',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 3788.06,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Episode no longer available',
    }, {
        'url': 'https://www.canvas.be/check-point/najaar-2016/de-politie-uw-vriend',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, display_id = mobj.group('site_id'), mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = strip_or_none(self._search_regex(
            r'<h1[^>]+class="video__body__header__title"[^>]*>(.+?)</h1>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None))

        video_id = self._html_search_regex(
            r'data-video=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage, 'video id',
            group='id')

        return {
            '_type': 'url_transparent',
            'url': 'https://mediazone.vrt.be/api/v1/%s/assets/%s' % (site_id, video_id),
            'ie_key': CanvasIE.ie_key(),
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
        }

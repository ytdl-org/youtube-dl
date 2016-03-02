from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import float_or_none


class CanvasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?canvas\.be/video/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.canvas.be/video/de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
        'md5': 'ea838375a547ac787d4064d8c7860a6c',
        'info_dict': {
            'id': 'mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
            'display_id': 'de-afspraak-veilt-voor-de-warmste-week',
            'ext': 'mp4',
            'title': 'De afspraak veilt voor de Warmste Week',
            'description': 'md5:24cb860c320dc2be7358e0e5aa317ba6',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 49.02,
        }
    }, {
        # with subtitles
        'url': 'http://www.canvas.be/video/panorama/2016/pieter-0167',
        'info_dict': {
            'id': 'mz-ast-5240ff21-2d30-4101-bba6-92b5ec67c625',
            'display_id': 'pieter-0167',
            'ext': 'mp4',
            'title': 'Pieter 0167',
            'description': 'md5:943cd30f48a5d29ba02c3a104dc4ec4e',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 2553.08,
            'subtitles': {
                'nl': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = self._search_regex(
            r'<h1[^>]+class="video__body__header__title"[^>]*>(.+?)</h1>',
            webpage, 'title', default=None) or self._og_search_title(webpage)

        video_id = self._html_search_regex(
            r'data-video=(["\'])(?P<id>.+?)\1', webpage, 'video id', group='id')

        data = self._download_json(
            'https://mediazone.vrt.be/api/v1/canvas/assets/%s' % video_id, display_id)

        formats = []
        for target in data['targetUrls']:
            format_url, format_type = target.get('url'), target.get('type')
            if not format_url or not format_type:
                continue
            if format_type == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, entry_protocol='m3u8_native',
                    ext='mp4', preference=0, fatal=False, m3u8_id=format_type))
            elif format_type == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url, display_id, f4m_id=format_type, fatal=False))
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
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'formats': formats,
            'duration': float_or_none(data.get('duration'), 1000),
            'thumbnail': data.get('posterImageUrl'),
            'subtitles': subtitles,
        }

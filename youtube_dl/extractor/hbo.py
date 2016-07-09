# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    xpath_element,
    int_or_none,
    parse_duration,
)


class HBOIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hbo\.com/video/video\.html\?.*vid=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.hbo.com/video/video.html?autoplay=true&g=u&vid=1437839',
        'md5': '1c33253f0c7782142c993c0ba62a8753',
        'info_dict': {
            'id': '1437839',
            'ext': 'mp4',
            'title': 'Ep. 64 Clip: Encryption',
        }
    }
    _FORMATS_INFO = {
        '1920': {
            'width': 1280,
            'height': 720,
        },
        '640': {
            'width': 768,
            'height': 432,
        },
        'highwifi': {
            'width': 640,
            'height': 360,
        },
        'high3g': {
            'width': 640,
            'height': 360,
        },
        'medwifi': {
            'width': 400,
            'height': 224,
        },
        'med3g': {
            'width': 400,
            'height': 224,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_xml(
            'http://render.lv3.hbo.com/data/content/global/videos/data/%s.xml' % video_id, video_id)
        title = xpath_text(video_data, 'title', 'title', True)

        formats = []
        for source in xpath_element(video_data, 'videos', 'sources', True):
            if source.tag == 'size':
                path = xpath_text(source, './/path')
                if not path:
                    continue
                width = source.attrib.get('width')
                format_info = self._FORMATS_INFO.get(width, {})
                height = format_info.get('height')
                fmt = {
                    'url': path,
                    'format_id': 'http%s' % ('-%dp' % height if height else ''),
                    'width': format_info.get('width'),
                    'height': height,
                }
                rtmp = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>.+))/(?P<playpath>mp4:.+)$', path)
                if rtmp:
                    fmt.update({
                        'url': rtmp.group('url'),
                        'play_path': rtmp.group('playpath'),
                        'app': rtmp.group('app'),
                        'ext': 'flv',
                        'format_id': fmt['format_id'].replace('http', 'rtmp'),
                    })
                formats.append(fmt)
            else:
                video_url = source.text
                if not video_url:
                    continue
                if source.tag == 'tarball':
                    formats.extend(self._extract_m3u8_formats(
                        video_url.replace('.tar', '/base_index_w8.m3u8'),
                        video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
                else:
                    format_info = self._FORMATS_INFO.get(source.tag, {})
                    formats.append({
                        'format_id': 'http-%s' % source.tag,
                        'url': video_url,
                        'width': format_info.get('width'),
                        'height': format_info.get('height'),
                    })
        self._sort_formats(formats, ('width', 'height', 'tbr', 'format_id'))

        thumbnails = []
        card_sizes = xpath_element(video_data, 'titleCardSizes')
        if card_sizes is not None:
            for size in card_sizes:
                path = xpath_text(size, 'path')
                if not path:
                    continue
                width = int_or_none(size.get('width'))
                thumbnails.append({
                    'id': width,
                    'url': path,
                    'width': width,
                })

        return {
            'id': video_id,
            'title': title,
            'duration': parse_duration(xpath_element(video_data, 'duration/tv14')),
            'formats': formats,
            'thumbnails': thumbnails,
        }

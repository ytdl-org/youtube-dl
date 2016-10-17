# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    ExtractorError,
    parse_iso8601,
    parse_duration,
)


class XuiteIE(InfoExtractor):
    IE_DESC = '隨意窩Xuite影音'
    _REGEX_BASE64 = r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?'
    _VALID_URL = r'https?://vlog\.xuite\.net/(?:play|embed)/(?P<id>%s)' % _REGEX_BASE64
    _TESTS = [{
        # Audio
        'url': 'http://vlog.xuite.net/play/RGkzc1ZULTM4NjA5MTQuZmx2',
        'md5': 'e79284c87b371424885448d11f6398c8',
        'info_dict': {
            'id': '3860914',
            'ext': 'mp3',
            'title': '孤單南半球-歐德陽',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 247.246,
            'timestamp': 1314932940,
            'upload_date': '20110902',
            'uploader': '阿能',
            'uploader_id': '15973816',
            'categories': ['個人短片'],
        },
    }, {
        # Video with only one format
        'url': 'http://vlog.xuite.net/play/WUxxR2xCLTI1OTI1MDk5LmZsdg==',
        'md5': '21f7b39c009b5a4615b4463df6eb7a46',
        'info_dict': {
            'id': '25925099',
            'ext': 'mp4',
            'title': 'BigBuckBunny_320x180',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 596.458,
            'timestamp': 1454242500,
            'upload_date': '20160131',
            'uploader': 'yan12125',
            'uploader_id': '12158353',
            'categories': ['個人短片'],
            'description': 'http://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4',
        },
    }, {
        # Video with two formats
        'url': 'http://vlog.xuite.net/play/bWo1N1pLLTIxMzAxMTcwLmZsdg==',
        'md5': '1166e0f461efe55b62e26a2d2a68e6de',
        'info_dict': {
            'id': '21301170',
            'ext': 'mp4',
            'title': '暗殺教室 02',
            'description': '字幕:【極影字幕社】',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 1384.907,
            'timestamp': 1421481240,
            'upload_date': '20150117',
            'uploader': '我只是想認真點',
            'uploader_id': '242127761',
            'categories': ['電玩動漫'],
        },
    }, {
        'url': 'http://vlog.xuite.net/play/S1dDUjdyLTMyOTc3NjcuZmx2/%E5%AD%AB%E7%87%95%E5%A7%BF-%E7%9C%BC%E6%B7%9A%E6%88%90%E8%A9%A9',
        'only_matching': True,
    }]

    @staticmethod
    def base64_decode_utf8(data):
        return base64.b64decode(data.encode('utf-8')).decode('utf-8')

    @staticmethod
    def base64_encode_utf8(data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def _extract_flv_config(self, media_id):
        base64_media_id = self.base64_encode_utf8(media_id)
        flv_config = self._download_xml(
            'http://vlog.xuite.net/flash/player?media=%s' % base64_media_id,
            'flv config')
        prop_dict = {}
        for prop in flv_config.findall('./property'):
            prop_id = self.base64_decode_utf8(prop.attrib['id'])
            # CDATA may be empty in flv config
            if not prop.text:
                continue
            encoded_content = self.base64_decode_utf8(prop.text)
            prop_dict[prop_id] = compat_urllib_parse_unquote(encoded_content)
        return prop_dict

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        error_msg = self._search_regex(
            r'<div id="error-message-content">([^<]+)',
            webpage, 'error message', default=None)
        if error_msg:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_msg),
                expected=True)

        video_id = self._html_search_regex(
            r'data-mediaid="(\d+)"', webpage, 'media id')
        flv_config = self._extract_flv_config(video_id)

        FORMATS = {
            'audio': 'mp3',
            'video': 'mp4',
        }

        formats = []
        for format_tag in ('src', 'hq_src'):
            video_url = flv_config.get(format_tag)
            if not video_url:
                continue
            format_id = self._search_regex(
                r'\bq=(.+?)\b', video_url, 'format id', default=format_tag)
            formats.append({
                'url': video_url,
                'ext': FORMATS.get(flv_config['type'], 'mp4'),
                'format_id': format_id,
                'height': int(format_id) if format_id.isnumeric() else None,
            })
        self._sort_formats(formats)

        timestamp = flv_config.get('publish_datetime')
        if timestamp:
            timestamp = parse_iso8601(timestamp + ' +0800', ' ')

        category = flv_config.get('category')
        categories = [category] if category else []

        return {
            'id': video_id,
            'title': flv_config['title'],
            'description': flv_config.get('description'),
            'thumbnail': flv_config.get('thumb'),
            'timestamp': timestamp,
            'uploader': flv_config.get('author_name'),
            'uploader_id': flv_config.get('author_id'),
            'duration': parse_duration(flv_config.get('duration')),
            'categories': categories,
            'formats': formats,
        }

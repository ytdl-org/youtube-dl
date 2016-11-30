# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    clean_html,
)


class ViuIE(InfoExtractor):
    IE_NAME = 'viu'
    _VALID_URL = r'https?://www\.viu\.com/ott/[a-z]+/[a-z\-]+/vod/(?P<id>[0-9]+)/'
    _TESTS = [{
        'url': 'http://www.viu.com/ott/sg/en-us/vod/3421/The%20Prime%20Minister%20and%20I',
        'info_dict': {
            'id': '3421',
            'ext': 'mp4',
            'title': 'The Prime Minister and I - Episode 17',
            'description': 'md5:1e7486a619b6399b25ba6a41c0fe5b2c',
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
        'skip': 'Geo-restricted to Singapore',
    }, {
        'url': 'http://www.viu.com/ott/hk/zh-hk/vod/7123/%E5%A4%A7%E4%BA%BA%E5%A5%B3%E5%AD%90',
        'info_dict': {
            'id': '7123',
            'ext': 'mp4',
            'title': '大人女子 - Episode 10',
            'description': 'md5:4eb0d8b08cf04fcdc6bbbeb16043434f',
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
        'skip': 'Geo-restricted to Hong Kong',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id, note='Downloading video page')

        mobj = re.search(
            r'<div class=["\']error-title[^<>]+?>(?P<err>.+?)</div>', webpage, flags=re.DOTALL)

        if mobj:
            raise ExtractorError(clean_html(mobj.group('err')), expected=True)

        config_js_url = self._search_regex(
            r'src=(["\'])(?P<api_url>.+?/js/config\.js)(?:\?.+?)?\1', webpage, 'config_js',
            group='api_url')

        config_js = self._download_webpage(
            'http://www.viu.com' + config_js_url, video_id, note='Downloading config js')
        
        # try to strip away commented code which contains test urls
        config_js = re.sub(r'^//.*?$', '', config_js, flags=re.MULTILINE)
        config_js = re.sub(r'/\*.*?\*/', '', config_js, flags=re.DOTALL)
        
        # Slightly different api_url between HK and SG config.js
        # http://www.viu.com/ott/hk/v1/js/config.js =>  '//www.viu.com/ott/hk/index.php?r='
        # http://www.viu.com/ott/sg/v1/js/config.js => 'http://www.viu.com/ott/sg/index.php?r='
        api_url = self._proto_relative_url(
            self._search_regex(
                r'var\s+api_url\s*=\s*(["\'])(?P<api_url>(?:https?:)?//.+?\?r=)\1',
                config_js, 'api_url', group='api_url'), scheme='http:')

        stream_info_url = self._proto_relative_url(
            self._search_regex(
                r'var\s+video_url\s*=\s*(["\'])(?P<video_url>(?:https?:)?//.+?\?ccs_product_id=)\1',
                config_js, 'video_url', group='video_url'), scheme='http:')

        video_info = self._download_json(
            api_url + 'vod/ajax-detail&platform_flag_label=web&product_id=' + video_id,
            video_id, note='Downloading video info').get('data', {})

        ccs_product_id = video_info.get('current_product', {}).get('ccs_product_id')

        if not ccs_product_id:
            raise ExtractorError('This video is not available in your region.', expected=True)

        stream_info = self._download_json(
            stream_info_url + ccs_product_id, video_id,
            note='Downloading stream info').get('data', {}).get('stream', {})

        formats = []
        for vid_format, stream_url in stream_info.get('url', {}).items():
            br = int_or_none(self._search_regex(
                r's(?P<br>[0-9]+)p', vid_format, 'bitrate', group='br'))
            formats.append({
                'format_id': vid_format,
                'url': stream_url,
                'vbr': br,
                'ext': 'mp4',
                'filesize': stream_info.get('size', {}).get(vid_format)
            })
        self._sort_formats(formats)

        subtitles = {}
        for sub in video_info.get('current_product', {}).get('subtitle', []):
            subtitles[sub.get('name')] = [{
                'url': sub.get('url'),
                'ext': 'srt',
            }]

        episode_info = next(
            p for p in video_info.get('series', {}).get('product', [])
            if p.get('product_id') == video_id)

        title = '%s - Episode %s' % (video_info.get('series', {}).get('name'),
                                     episode_info.get('number'))
        description = episode_info.get('description')
        thumbnail = episode_info.get('cover_image_url')
        duration = int_or_none(stream_info.get('duration'))
        series = video_info.get('series', {}).get('name')
        episode_title = episode_info.get('synopsis')
        episode_num = int_or_none(episode_info.get('number'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'episode': episode_title,
            'episode_number': episode_num,
            'duration': duration,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }

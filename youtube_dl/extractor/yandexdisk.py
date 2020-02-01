# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    try_get,
    urlencode_postdata,
)


class YandexDiskIE(InfoExtractor):
    _VALID_URL = r'https?://yadi\.sk/[di]/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://yadi.sk/i/VdOeDou8eZs6Y',
        'md5': '33955d7ae052f15853dc41f35f17581c',
        'info_dict': {
            'id': 'VdOeDou8eZs6Y',
            'ext': 'mp4',
            'title': '4.mp4',
            'duration': 168.6,
            'uploader': 'y.botova',
            'uploader_id': '300043621',
            'view_count': int,
        },
    }, {
        'url': 'https://yadi.sk/d/h3WAXvDS3Li3Ce',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        status = self._download_webpage(
            'https://disk.yandex.com/auth/status', video_id, query={
                'urlOrigin': url,
                'source': 'public',
                'md5': 'false',
            })

        sk = self._search_regex(
            r'(["\'])sk(?:External)?\1\s*:\s*(["\'])(?P<value>(?:(?!\2).)+)\2',
            status, 'sk', group='value')

        webpage = self._download_webpage(url, video_id)

        models = self._parse_json(
            self._search_regex(
                r'<script[^>]+id=["\']models-client[^>]+>\s*(\[.+?\])\s*</script',
                webpage, 'video JSON'),
            video_id)

        data = next(
            model['data'] for model in models
            if model.get('model') == 'resource')

        video_hash = data['id']
        title = data['name']

        models = self._download_json(
            'https://disk.yandex.com/models/', video_id,
            data=urlencode_postdata({
                '_model.0': 'videoInfo',
                'id.0': video_hash,
                '_model.1': 'do-get-resource-url',
                'id.1': video_hash,
                'version': '13.6',
                'sk': sk,
            }), query={'_m': 'videoInfo'})['models']

        videos = try_get(models, lambda x: x[0]['data']['videos'], list) or []
        source_url = try_get(
            models, lambda x: x[1]['data']['file'], compat_str)

        formats = []
        if source_url:
            formats.append({
                'url': source_url,
                'format_id': 'source',
                'ext': determine_ext(title, 'mp4'),
                'quality': 1,
            })
        for video in videos:
            format_url = video.get('url')
            if not format_url:
                continue
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': format_url,
                })
        self._sort_formats(formats)

        duration = float_or_none(try_get(
            models, lambda x: x[0]['data']['duration']), 1000)
        uploader = try_get(
            data, lambda x: x['user']['display_name'], compat_str)
        uploader_id = try_get(
            data, lambda x: x['user']['uid'], compat_str)
        view_count = int_or_none(try_get(
            data, lambda x: x['meta']['views_counter']))

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'formats': formats,
        }

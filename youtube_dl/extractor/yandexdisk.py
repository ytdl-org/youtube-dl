# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    urljoin,
)


class YandexDiskIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:
            (?:www\.)?yadi\.sk|
            disk\.yandex\.
                (?:
                    az|
                    by|
                    co(?:m(?:\.(?:am|ge|tr))?|\.il)|
                    ee|
                    fr|
                    k[gz]|
                    l[tv]|
                    md|
                    t[jm]|
                    u[az]|
                    ru
                )
        )/(?:[di]/|public.*?\bhash=)(?P<id>[^/?#&]+)'''

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
            'timestamp': 1421396809,
            'upload_date': '20150116',
            'view_count': int,
        },
    }, {
        'url': 'https://yadi.sk/d/h3WAXvDS3Li3Ce',
        'only_matching': True,
    }, {
        'url': 'https://yadi.sk/public?hash=5DZ296JK9GWCLp02f6jrObjnctjRxMs8L6%2B%2FuhNqk38%3D',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            resource = self._download_json(
                'https://cloud-api.yandex.net/v1/disk/public/resources',
                video_id, query={'public_key': url})
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error_description = self._parse_json(
                    e.cause.read().decode(), video_id)['description']
                raise ExtractorError(error_description, expected=True)
            raise

        title = resource['name']
        public_url = resource.get('public_url')
        if public_url:
            video_id = self._match_id(public_url)

        self._set_cookie('yadi.sk', 'yandexuid', '0')

        def call_api(action):
            return (self._download_json(
                urljoin(url, '/public/api/') + action, video_id, data=json.dumps({
                    'hash': url,
                    # obtain sk if needed from call_api('check-auth') while
                    # the yandexuid cookie is set and sending an empty JSON object
                    'sk': 'ya6b52f8c6b12abe91a66d22d3a31084b'
                }).encode(), headers={
                    'Content-Type': 'text/plain',
                }, fatal=False) or {}).get('data') or {}

        formats = []
        source_url = resource.get('file')
        if not source_url:
            source_url = call_api('download-url').get('url')
        if source_url:
            formats.append({
                'url': source_url,
                'format_id': 'source',
                'ext': determine_ext(title, mimetype2ext(resource.get('mime_type')) or 'mp4'),
                'quality': 1,
                'filesize': int_or_none(resource.get('size'))
            })

        video_streams = call_api('get-video-streams')
        for video in (video_streams.get('videos') or []):
            format_url = video.get('url')
            if not format_url:
                continue
            if video.get('dimension') == 'adaptive':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                size = video.get('size') or {}
                height = int_or_none(size.get('height'))
                format_id = 'hls'
                if height:
                    format_id += '-%dp' % height
                formats.append({
                    'ext': 'mp4',
                    'format_id': format_id,
                    'height': height,
                    'protocol': 'm3u8_native',
                    'url': format_url,
                    'width': int_or_none(size.get('width')),
                })
        self._sort_formats(formats)

        owner = resource.get('owner') or {}

        return {
            'id': video_id,
            'title': title,
            'duration': float_or_none(video_streams.get('duration'), 1000),
            'uploader': owner.get('display_name'),
            'uploader_id': owner.get('uid'),
            'view_count': int_or_none(resource.get('views_count')),
            'timestamp': parse_iso8601(resource.get('created')),
            'formats': formats,
        }

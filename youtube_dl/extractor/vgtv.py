# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import float_or_none


class VGTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?vgtv\.no/#!/(?:.*)/(?P<id>[0-9]+)'
    _TESTS = [
        {
            # streamType: vod
            'url': 'http://www.vgtv.no/#!/video/84196/hevnen-er-soet-episode-10-abu',
            'md5': 'b8be7a234cebb840c0d512c78013e02f',
            'info_dict': {
                'id': '84196',
                'ext': 'mp4',
                'title': 'Hevnen er søt: Episode 10 - Abu',
                'description': 'md5:e25e4badb5f544b04341e14abdc72234',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 648.000,
                'timestamp': 1404626400,
                'upload_date': '20140706',
                'view_count': int,
            },
        },
        {
            # streamType: wasLive
            'url': 'http://www.vgtv.no/#!/live/100764/opptak-vgtv-foelger-em-kvalifiseringen',
            'info_dict': {
                'id': '100764',
                'ext': 'flv',
                'title': 'OPPTAK: VGTV følger EM-kvalifiseringen',
                'description': 'md5:3772d9c0dc2dff92a886b60039a7d4d3',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 9103.0,
                'timestamp': 1410113864,
                'upload_date': '20140907',
                'view_count': int,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            # streamType: live
            'url': 'http://www.vgtv.no/#!/live/100015/direkte-her-kan-du-se-laksen-live-fra-suldalslaagen',
            'info_dict': {
                'id': '100015',
                'ext': 'flv',
                'title': 'DIREKTE: Her kan du se laksen live fra Suldalslågen!',
                'description': 'md5:9a60cc23fa349f761628924e56eeec2d',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 0,
                'timestamp': 1407423348,
                'upload_date': '20140807',
                'view_count': int,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'http://svp.vg.no/svp/api/v1/vgtv/assets/%s?appName=vgtv-website' % video_id,
            video_id, 'Downloading media JSON')

        streams = data['streamUrls']

        formats = []

        hls_url = streams.get('hls')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(hls_url, video_id, 'mp4'))

        hds_url = streams.get('hds')
        if hds_url:
            formats.extend(self._extract_f4m_formats(hds_url + '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18', video_id))

        mp4_url = streams.get('mp4')
        if mp4_url:
            _url = hls_url or hds_url
            MP4_URL_TEMPLATE = '%s/%%s.%s' % (mp4_url.rpartition('/')[0], mp4_url.rpartition('.')[-1])
            for mp4_format in _url.split(','):
                m = re.search('(?P<width>\d+)_(?P<height>\d+)_(?P<vbr>\d+)', mp4_format)
                if not m:
                    continue
                width = int(m.group('width'))
                height = int(m.group('height'))
                vbr = int(m.group('vbr'))
                formats.append({
                    'url': MP4_URL_TEMPLATE % mp4_format,
                    'format_id': 'mp4-%s' % vbr,
                    'width': width,
                    'height': height,
                    'vbr': vbr,
                    'preference': 1,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': data['title'],
            'description': data['description'],
            'thumbnail': data['images']['main'] + '?t[]=900x506q80',
            'timestamp': data['published'],
            'duration': float_or_none(data['duration'], 1000),
            'view_count': data['displays'],
            'formats': formats,
        }

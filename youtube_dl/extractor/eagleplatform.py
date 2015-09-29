# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


class EaglePlatformIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        eagleplatform:(?P<custom_host>[^/]+):|
                        https?://(?P<host>.+?\.media\.eagleplatform\.com)/index/player\?.*\brecord_id=
                    )
                    (?P<id>\d+)
                '''
    _TESTS = [{
        # http://lenta.ru/news/2015/03/06/navalny/
        'url': 'http://lentaru.media.eagleplatform.com/index/player?player=new&record_id=227304&player_template_id=5201',
        'md5': '70f5187fb620f2c1d503b3b22fd4efe3',
        'info_dict': {
            'id': '227304',
            'ext': 'mp4',
            'title': 'Навальный вышел на свободу',
            'description': 'md5:d97861ac9ae77377f3f20eaf9d04b4f5',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 87,
            'view_count': int,
            'age_limit': 0,
        },
    }, {
        # http://muz-tv.ru/play/7129/
        # http://media.clipyou.ru/index/player?record_id=12820&width=730&height=415&autoplay=true
        'url': 'eagleplatform:media.clipyou.ru:12820',
        'md5': '90b26344ba442c8e44aa4cf8f301164a',
        'info_dict': {
            'id': '12820',
            'ext': 'mp4',
            'title': "'O Sole Mio",
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 216,
            'view_count': int,
        },
        'skip': 'Georestricted',
    }]

    @staticmethod
    def _handle_error(response):
        status = int_or_none(response.get('status', 200))
        if status != 200:
            raise ExtractorError(' '.join(response['errors']), expected=True)

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata'):
        response = super(EaglePlatformIE, self)._download_json(url_or_request, video_id, note)
        self._handle_error(response)
        return response

    def _get_video_url(self, url_or_request, video_id, note='Downloading JSON metadata'):
        return self._download_json(url_or_request, video_id, note)['data'][0]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host, video_id = mobj.group('custom_host') or mobj.group('host'), mobj.group('id')

        player_data = self._download_json(
            'http://%s/api/player_data?id=%s' % (host, video_id), video_id)

        media = player_data['data']['playlist']['viewports'][0]['medialist'][0]

        title = media['title']
        description = media.get('description')
        thumbnail = self._proto_relative_url(media.get('snapshot'), 'http:')
        duration = int_or_none(media.get('duration'))
        view_count = int_or_none(media.get('views'))

        age_restriction = media.get('age_restriction')
        age_limit = None
        if age_restriction:
            age_limit = 0 if age_restriction == 'allow_all' else 18

        secure_m3u8 = self._proto_relative_url(media['sources']['secure_m3u8']['auto'], 'http:')

        m3u8_url = self._get_video_url(secure_m3u8, video_id, 'Downloading m3u8 JSON')
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id,
            'mp4', entry_protocol='m3u8_native')

        mp4_url = self._get_video_url(
            # Secure mp4 URL is constructed according to Player.prototype.mp4 from
            # http://lentaru.media.eagleplatform.com/player/player.js
            re.sub(r'm3u8|hlsvod|hls|f4m', 'mp4', secure_m3u8),
            video_id, 'Downloading mp4 JSON')
        formats.append({'url': mp4_url, 'format_id': 'mp4'})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    ExtractorError,
    int_or_none,
    url_basename,
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
        # Not checking MD5 as sometimes the direct HTTP link results in 404 and HLS is used
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
        'md5': '358597369cf8ba56675c1df15e7af624',
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
    def _extract_url(webpage):
        # Regular iframe embedding
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//.+?\.media\.eagleplatform\.com/index/player\?.+?)\1',
            webpage)
        if mobj is not None:
            return mobj.group('url')
        # Basic usage embedding (see http://dultonmedia.github.io/eplayer/)
        mobj = re.search(
            r'''(?xs)
                    <script[^>]+
                        src=(?P<q1>["\'])(?:https?:)?//(?P<host>.+?\.media\.eagleplatform\.com)/player/player\.js(?P=q1)
                    .+?
                    <div[^>]+
                        class=(?P<q2>["\'])eagleplayer(?P=q2)[^>]+
                        data-id=["\'](?P<id>\d+)
            ''', webpage)
        if mobj is not None:
            return 'eagleplatform:%(host)s:%(id)s' % mobj.groupdict()

    @staticmethod
    def _handle_error(response):
        status = int_or_none(response.get('status', 200))
        if status != 200:
            raise ExtractorError(' '.join(response['errors']), expected=True)

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata'):
        try:
            response = super(EaglePlatformIE, self)._download_json(url_or_request, video_id, note)
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError):
                response = self._parse_json(ee.cause.read().decode('utf-8'), video_id)
                self._handle_error(response)
            raise
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

        formats = []

        m3u8_url = self._get_video_url(secure_m3u8, video_id, 'Downloading m3u8 JSON')
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id,
            'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        formats.extend(m3u8_formats)

        mp4_url = self._get_video_url(
            # Secure mp4 URL is constructed according to Player.prototype.mp4 from
            # http://lentaru.media.eagleplatform.com/player/player.js
            re.sub(r'm3u8|hlsvod|hls|f4m', 'mp4', secure_m3u8),
            video_id, 'Downloading mp4 JSON')
        mp4_url_basename = url_basename(mp4_url)
        for m3u8_format in m3u8_formats:
            mobj = re.search('/([^/]+)/index\.m3u8', m3u8_format['url'])
            if mobj:
                http_format = m3u8_format.copy()
                video_url = mp4_url.replace(mp4_url_basename, mobj.group(1))
                if not self._is_valid_url(video_url, video_id):
                    continue
                http_format.update({
                    'url': video_url,
                    'format_id': m3u8_format['format_id'].replace('hls', 'http'),
                    'protocol': 'http',
                })
                formats.append(http_format)

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

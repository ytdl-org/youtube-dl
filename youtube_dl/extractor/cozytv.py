# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    unified_timestamp,
    ExtractorError,
)


class CozyTVBaseIE(InfoExtractor):
    _API_BASE = 'https://api.cozy.tv'

    def _join_url(self, *parts):
        return '/'.join(parts).rstrip('/')

    def _user_status(self, user, video_id):
        url = self._join_url(self._API_BASE, 'cache', user, 'status')
        return self._download_json(url, video_id)

    def _extend_formats(self, formats, cdn_url, video_id, live=False):
        formats.extend(self._extract_m3u8_formats(
            cdn_url + '/index.m3u8',
            video_id,
            ext='mp4',
            m3u8_id='hls',
            preference=-1,
            live=live))
        formats.extend(self._extract_m3u8_formats(
            cdn_url + '/index-ts-audio.m3u8',
            video_id,
            ext='mp4',
            m3u8_id='hls-audio',
            preference=-2,
            fatal=False,
            live=live))
        self._sort_formats(formats)


class CozyTVStreamIE(CozyTVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cozy\.tv/(?P<user>[^/?#]+)'
    _TEST = {
        'url': 'https://cozy.tv/alexjones',
        'info_dict': {
            'id': 'alexjones',
            'title': 'The Alex Jones Show - Infowars.com',
            'ext': 'mp4',
            'uploader': 'AlexJones',
            'timestamp': 1658422904,
            'upload_date': '20220721',
            'uploader_id': 'alexjones',
            'uploader_url': 'https://cozy.tv/alexjones',
            'view_count': int,
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id, user = re.match(self._VALID_URL, url).group('user', 'user')
        user_status = self._user_status(user, video_id)
        is_live = user_status['isLive']

        if is_live is None:
            raise ExtractorError('%s is offline' % user, expected=True)

        cdn_url = self._join_url(user_status['livecdns'][0], 'live', user)

        info = {
            'id': video_id,
            'title': user_status['title'],
        }

        timestamp = unified_timestamp(is_live)
        formats = []
        self._extend_formats(formats, cdn_url, video_id, live=True)

        info.update({
            'display_id': video_id,
            'formats': formats,
            'timestamp': timestamp,
            'uploader': user_status.get('displayName') or user,
            'uploader_id': user,
            'uploader_url': 'https://cozy.tv/' + user,
            'view_count': int_or_none(user_status.get('viewers')),
            'is_live': True,
        })

        return info


class CozyTVReplayIE(CozyTVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cozy\.tv/(?P<user>[^/]+)/replays/(?P<id>\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])(?:_\d+)?)'
    _TESTS = [
        {
            'url': 'https://cozy.tv/althype/replays/2022-05-24_2',
            'info_dict': {
                'id': '628d070e3f2f1a99756b6c2f',
                'title': 'Secret Stream: Making Video',
                'ext': 'mp4',
                'display_id': '2022-05-24_2',
                'thumbnail': r're:^https?://.*/replays/althype/2022-05-24_2/thumb\.webp$',
                'uploader': 'AltHype',
                'timestamp': 1653409506,
                'upload_date': '20220524',
                'uploader_id': 'althype',
                'uploader_url': 'https://cozy.tv/althype',
                'duration': 9303.0,
                'view_count': 217,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://cozy.tv/nick/replays/2022-07-28',
            'info_dict': {
                'id': '62e23d1c4a22de6fb37b83f5',
                'title': 'GAY PANDEMIC: Biden Admin To Declare MONKEYPOX EMERGENCY | America First Ep. 1037',
                'ext': 'mp4',
                'display_id': '2022-07-28',
                'thumbnail': r're:^https?://.*/replays/nick/2022-07-28/thumb\.webp$',
                'uploader': 'Nick',
                'timestamp': 1658993895,
                'upload_date': '20220728',
                'uploader_id': 'nick',
                'uploader_url': 'https://cozy.tv/nick',
                'duration': 16410.0,
                'view_count': 6281,
            },
            'params': {
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id, user = re.match(self._VALID_URL, url).group('id', 'user')
        user_status = self._user_status(user, video_id)
        data_url = self._join_url(self._API_BASE, 'cache', user, 'replay', video_id)
        data = self._download_json(data_url, video_id)

        cdn_url = self._join_url(data['cdns'][0], 'replays', user, video_id)

        info = {
            'id': data.get('_id') or video_id,
            'title': data['title'],
        }

        timestamp = unified_timestamp(data.get('date'))
        formats = []
        self._extend_formats(formats, cdn_url, video_id)

        info.update({
            'display_id': video_id,
            'duration': float_or_none(data.get('duration')),
            'formats': formats,
            'thumbnail': cdn_url + '/thumb.webp',
            'timestamp': timestamp,
            'uploader': user_status.get('displayName') or user,
            'uploader_id': user,
            'uploader_url': 'https://cozy.tv/' + user,
            'view_count': int_or_none(data.get('peakViewers')),
        })

        return info

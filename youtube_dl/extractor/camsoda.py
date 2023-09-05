# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
import random
from ..utils import ExtractorError


class CamsodaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?camsoda\.com/(?P<id>\S+)'
    _TEST = {
        'url': 'https://camsoda.com/valeryromero',
        'info_dict': {
            'id': 'valeryromero',
            'ext': 'mp4',
            'title': 're:^valeryromero [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'User is offline',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        user_data = self._download_json(
            'https://www.camsoda.com/api/v1/user/%s' % video_id,
            video_id, 'Downloading user data')

        if not user_data.get('status'):
            raise ExtractorError('No broadcaster found', expected=True)

        user = user_data.get('user') if isinstance(user_data.get('user'), dict) else None
        if user:
            thumb = user.get('thumb') or user.get('profile_picture')
        else:
            thumb = None

        video_data = self._download_json(
            'https://www.camsoda.com/api/v1/video/vtoken/%s' % video_id, video_id,
            'Downloading stream token', query={
                'username': 'guest_%s' % compat_str(random.randint(1000, 99999)),
            })

        if not video_data.get('edge_servers'):
            raise ExtractorError('Stream is not available', expected=True)

        m3u8_url = 'https://%s/%s/mp4:%s_aac/playlist.m3u8?token=%s' % (
            video_data['edge_servers'][0], video_data['app'],
            video_data['stream_name'], video_data['token'])

        formats = []
        formats.extend(self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', live=True))

        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'is_live': True,
            'thumbnail': thumb,
            'formats': formats,
            'age_limit': 18,
        }

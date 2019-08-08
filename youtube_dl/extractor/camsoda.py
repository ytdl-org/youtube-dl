# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import random
from ..utils import ExtractorError


class CamsodaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?camsoda\.com/(?P<id>\S+)'
    _TEST = {
        'url': 'https://camsoda.com/bustynasha',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 're:^bustynasha [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'is_live': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        user_data = self._download_json('https://www.camsoda.com/api/v1/user/%s' % video_id, 'Downloading user data', video_id)

        if not user_data.get('status'):
            raise ExtractorError('Stream is not available', expected=True)

        # TODO more code goes here, for example ...
        video_data = self._download_json('https://www.camsoda.com/api/v1/video/vtoken/%s?username=guest_%s' %
                                         (video_id, str(random.randint(1000, 99999))), 'Downloading second json', video_id)

        HLS_URL_VIDEO = 'https://{server}/{app}/mp4:{stream_name}_aac/playlist.m3u8?token={token}'
        hls_url = HLS_URL_VIDEO.format(
            server=video_data['edge_servers'][0],
            app=video_data['app'],
            stream_name=video_data['stream_name'],
            token=video_data['token']
        )

        formats = []
        formats.extend(self._extract_m3u8_formats(
            hls_url, video_id, ext='mp4',
            fatal=False, live=True)
        )

        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'is_live': True,
            'formats': formats,
        }

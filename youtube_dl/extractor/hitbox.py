# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class HitboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hitbox\.tv/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.hitbox.tv/video/358062',
        'info_dict': {
            'id': '358062',
            'title': 'Megaman',
            'alt_title': 'Megaman',
            'description': '',
            'ext': 'mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 3834,
            'resolution': 'SD 480p',
            'uploader_id': 'supergreatfriend',
            'view_count': int,
            'upload_date': '20141225',
            'categories': [None],
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.hitbox.tv/video/203213',
        'info_dict': {
            'id': '203213',
            'title': 'hitbox @ gamescom, Sub Button Hype extended, Giveaway - hitbox News Update with Oxy',
            'alt_title': 'hitboxlive - Aug 9th #6',
            'description': '',
            'ext': 'mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 215,
            'resolution': 'HD 720p',
            'uploader_id': 'hitboxlive',
            'view_count': int,
            'upload_date': '20140809',
            'categories': ['Live Show'],
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        thumb_base = 'https://edge.sf.hitbox.tv'
        metadata = self._download_json(
            'https://www.hitbox.tv/api/media/video/%s' % (video_id), video_id
        )

        video_meta = metadata.get('video', [])[0]
        title = video_meta.get('media_status')
        alt_title = video_meta.get('media_title')
        description = video_meta.get('media_description')
        duration = int(float(video_meta.get('media_duration')))
        uploader = video_meta.get('media_user_name')
        views = int(video_meta.get('media_views'))
        upload_date = unified_strdate(video_meta.get('media_date_added'))
        categories = [video_meta.get('category_name')]
        thumbs = [
            {'url': thumb_base + video_meta.get('media_thumbnail'),
             'width': 320,
             'height': 180},
            {'url': thumb_base + video_meta.get('media_thumbnail_large'),
             'width': 768,
             'height': 432},
        ]

        player_config = self._download_json(
            'https://www.hitbox.tv/api/player/config/video/%s' % (video_id),
            video_id
        )

        clip = player_config.get('clip')
        video_url = clip.get('url')
        res = clip.get('bitrates', [])[0].get('label')

        return {
            'id': video_id,
            'title': title,
            'alt_title': alt_title,
            'description': description,
            'url': video_url,
            'ext': 'mp4',
            'thumbnails': thumbs,
            'duration': duration,
            'resolution': res,
            'uploader_id': uploader,
            'view_count': views,
            'upload_date': upload_date,
            'categories': categories,
            'protocol': 'm3u8',
        }

# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class HitboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hitbox\.tv/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.hitbox.tv/video/203213',
        'info_dict': {
            'id': '203213',
            'title': 'hitbox @ gamescom, Sub Button Hype extended, Giveaway - hitbox News Update with Oxy',
            'alt_title': 'hitboxlive - Aug 9th #6',
            'description': '\n',
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
    }

    def _extract_metadata(self, url, video_id):
        thumb_base = 'https://edge.sf.hitbox.tv'
        metadata = self._download_json(
            '%s/%s' % (url, video_id), video_id
        )

        date = 'media_live_since'
        media_type = 'livestream'
        if metadata.get('media_type') == 'video':
            media_type = 'video'
            date = 'media_date_added'

        video_meta = metadata.get(media_type, [])[0]
        title = video_meta.get('media_status')
        alt_title = video_meta.get('media_title')
        description = video_meta.get('media_description_md')
        duration = int(float(video_meta.get('media_duration')))
        uploader = video_meta.get('media_user_name')
        views = int(video_meta.get('media_views'))
        upload_date = unified_strdate(video_meta.get(date))
        categories = [video_meta.get('category_name')]
        thumbs = [
            {'url': thumb_base + video_meta.get('media_thumbnail'),
             'width': 320,
             'height': 180},
            {'url': thumb_base + video_meta.get('media_thumbnail_large'),
             'width': 768,
             'height': 432},
        ]

        return {
            'id': video_id,
            'title': title,
            'alt_title': alt_title,
            'description': description,
            'ext': 'mp4',
            'thumbnails': thumbs,
            'duration': duration,
            'uploader_id': uploader,
            'view_count': views,
            'upload_date': upload_date,
            'categories': categories,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        metadata = self._extract_metadata(
            'https://www.hitbox.tv/api/media/video',
            video_id
        )

        player_config = self._download_json(
            'https://www.hitbox.tv/api/player/config/video/%s' % (video_id),
            video_id
        )

        clip = player_config.get('clip')
        video_url = clip.get('url')
        res = clip.get('bitrates', [])[0].get('label')

        metadata['resolution'] = res
        metadata['url'] = video_url
        metadata['protocol'] = 'm3u8'

        return metadata


class HitboxLiveIE(HitboxIE):
    _VALID_URL = r'https?://(?:www\.)?hitbox\.tv/(?!video)(?P<id>.+)'
    _TEST = {
        'url': 'http://www.hitbox.tv/dimak',
        'info_dict': {
            'id': 'dimak',
            'ext': 'mp4',
            'description': str,
            'upload_date': str,
            'title': str,
            'uploader_id': 'Dimak',
        },
        'params': {
            # live
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        metadata = self._extract_metadata(
            'https://www.hitbox.tv/api/media/live',
            video_id
        )

        player_config = self._download_json(
            'https://www.hitbox.tv/api/player/config/live/%s' % (video_id),
            video_id
        )

        formats = []
        cdns = player_config.get('cdns')
        servers = []
        for cdn in cdns:
            base_url = cdn.get('netConnectionUrl')
            host = re.search('.+\.([^\.]+\.[^\./]+)/.+', base_url).group(1)
            if base_url not in servers:
                servers.append(base_url)
                for stream in cdn.get('bitrates'):
                    label = stream.get('label')
                    if label != 'Auto':
                        formats.append({
                            'url': '%s/%s' % (base_url, stream.get('url')),
                            'ext': 'mp4',
                            'vbr': stream.get('bitrate'),
                            'resolution': label,
                            'rtmp_live': True,
                            'format_note': host,
                            'page_url': url,
                            'player_url': 'http://www.hitbox.tv/static/player/flowplayer/flowplayer.commercial-3.2.16.swf',
                        })

        self._sort_formats(formats)
        metadata['formats'] = formats
        metadata['is_live'] = True
        metadata['title'] = self._live_title(metadata.get('title'))
        return metadata

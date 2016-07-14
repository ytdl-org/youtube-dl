from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    qualities,
)


class KamcordIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kamcord\.com/v/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.kamcord.com/v/hNYRduDgWb4',
        'md5': 'c3180e8a9cfac2e86e1b88cb8751b54c',
        'info_dict': {
            'id': 'hNYRduDgWb4',
            'ext': 'mp4',
            'title': 'Drinking Madness',
            'uploader': 'jacksfilms',
            'uploader_id': '3044562',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video = self._parse_json(
            self._search_regex(
                r'window\.__props\s*=\s*({.+?});?(?:\n|\s*</script)',
                webpage, 'video'),
            video_id)['video']

        title = video['title']

        formats = self._extract_m3u8_formats(
            video['play']['hls'], video_id, 'mp4', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        uploader = video.get('user', {}).get('username')
        uploader_id = video.get('user', {}).get('id')

        view_count = int_or_none(video.get('viewCount'))
        like_count = int_or_none(video.get('heartCount'))
        comment_count = int_or_none(video.get('messageCount'))

        preference_key = qualities(('small', 'medium', 'large'))

        thumbnails = [{
            'url': thumbnail_url,
            'id': thumbnail_id,
            'preference': preference_key(thumbnail_id),
        } for thumbnail_id, thumbnail_url in (video.get('thumbnail') or {}).items()
            if isinstance(thumbnail_id, compat_str) and isinstance(thumbnail_url, compat_str)]

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'thumbnails': thumbnails,
            'formats': formats,
        }

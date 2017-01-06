from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    unified_strdate,
)
from ..compat import compat_str


class HitRecordIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hitrecord\.org/records/(?P<id>\d+)'

    _TEST = {
        'url': 'https://hitrecord.org/records/2954362',
        'md5': 'fe1cdc2023bce0bbb95c39c57426aa71',
        'info_dict': {
            'id': '2954362',
            'ext': 'mp4',
            'title': 'A Very Different World (HITRECORD x ACLU)',
            'description': 'md5:e62defaffab5075a5277736bead95a3d',
            'release_date': '20160818',
            'timestamp': 1471557582,
            'uploader': 'Zuzi.C12',
            'uploader_id': '362811',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = self._download_json('https://hitrecord.org/api/web/records/' + video_id, video_id)
        user_info = video_info.get('user', {})

        return {
            'id': video_id,
            'title': video_info['title'],
            'url': video_info['source_url']['mp4_url'],
            'description': clean_html(video_info.get('body')),
            'uploader': user_info.get('username'),
            'uploader_id': compat_str(user_info.get('id')),
            'release_date': unified_strdate(video_info.get('created_at')),
            'timestamp': video_info.get('created_at_i'),
            'view_count': int_or_none(video_info.get('total_views_count')),
            'like_count': int_or_none(video_info.get('hearts_count')),
            'comment_count': int_or_none(video_info.get('comments_count')),
            'tags': [tag.get('text') for tag in video_info.get('tags', [])],
        }

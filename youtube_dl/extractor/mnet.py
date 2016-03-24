# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    parse_iso8601,
)


class MnetIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mnet\.(?:com|interest\.me)/tv/vod/(?:.*?\bclip_id=)?(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.mnet.com/tv/vod/171008',
            'md5': '6abd7a837fa9fe56d22709a60b19bffb',
            'info_dict': {
                'id': '171008',
                'title': 'SS_이해인@히든박스',
                'description': 'md5:b9efa592c3918b615ba69fe9f8a05c55',
                'duration': 88,
                'upload_date': '20151231',
                'timestamp': 1451564040,
                'age_limit': 0,
                'thumbnails': 'mincount:5',
                'ext': 'flv',
            },
        },
        {
            'url': 'http://mnet.interest.me/tv/vod/172790',
            'only_matching': True,
        },
        {
            'url': 'http://www.mnet.com/tv/vod/vod_view.asp?clip_id=172790&tabMenu=',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info_url = 'http://content.api.mnet.com/player/vodConfig?id=%s' % video_id
        info = self._download_json(info_url, video_id)
        info = info['data']['info']

        title = info['title']
        rtmp_info_url = info['cdn'] + 'CLIP'
        rtmp_info = self._download_json(rtmp_info_url, video_id)
        file_url = rtmp_info['serverurl'] + rtmp_info['fileurl']
        description = info.get('ment')
        duration = parse_duration(info.get('time'))
        timestamp = parse_iso8601(info.get('date'), delimiter=' ')
        age_limit = info.get('adult')
        if age_limit is not None:
            age_limit = 0 if age_limit == 'N' else 18
        thumbnails = [
            {
                'id': thumb_format,
                'url': thumb['url'],
                'width': int_or_none(thumb.get('width')),
                'height': int_or_none(thumb.get('height')),
            }
            for (thumb_format, thumb) in info.get('cover', {}).items()
        ]

        return {
            'id': video_id,
            'title': title,
            'url': file_url,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'age_limit': age_limit,
            'thumbnails': thumbnails,
            'ext': 'flv',
        }

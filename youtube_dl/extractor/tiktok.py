# coding: utf-8
from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class TikTokIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/.*/video/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@ben_brainard/video/6858321293117312262',
        # 'md5': 'd584b572e92fcd48888051f238022420',
        'info_dict': {
            'id': '6858321293117312262',
            'ext': 'mp4',
            'title': 'ben_brainard',
            'description': 'Hurricane... hurricane... hurricane... I got nothing.',
            'uploader': 'ben_brainard',
            'timestamp': 1596827366,
            'upload_date': '20200807',
            'comment_count': int
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        # print webpage
        description = self._search_regex(r'<title[^>]*>([^<]+)</title>', webpage, 'description')
        mediaUrl = self._search_regex(r'"video":{"urls":\["([^"]+)"', webpage, 'url')
        # data = self._parse_html5_media_entries(url,webpage,video_id)
        uploader = self._search_regex(r'"authorName":"([^"]+)"', webpage, 'uploader')
        commentCount = self._search_regex(r'"commentCount":([^,]+)', webpage, 'comment_count')
        viewCount = self._search_regex(r'"playCount":([^,]+)', webpage, 'view_count')
        timestamp = self._search_regex(r'"createTime":"([^"]+)"', webpage, 'timestamp')

        return {
            'id': video_id,
            'url': mediaUrl,
            'title': uploader,
            'description': description,
            'ext': 'mp4',
            'uploader': uploader,
            'comment_count': int_or_none(commentCount),
            'view_count': int_or_none(viewCount),
            'timestamp': int_or_none(timestamp)
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get
)


class TikTokIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@.+/video/(?P<id>[0-9]+)+'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zoey.aune/video/6813765043914624262?lang=en',
        'md5': '210b3d6356ea90977fcb62a4db343b8b',
        'info_dict': {
            'comment_count': int,
            'creator': 'Zoey',
            'description': 'md5:b22dea1b2dd4e18258ebe42cf5571a97',
            'duration': 10,
            'ext': 'mp4',
            'formats': list,
            'width': 576,
            'height': 1024,
            'id': '6813765043914624262',
            'like_count': int,
            'repost_count': int,
            'thumbnail': r're:^https?://[\w\/\.\-]+(~[\w\-]+\.image)?',
            'thumbnails': list,
            'timestamp': 1586453303,
            'title': 'md5:b22dea1b2dd4e18258ebe42cf5571a97',
            'upload_date': '20200409',
            'uploader': 'zoey.aune',
            'uploader_id': '6651338645989621765',
            'uploader_url': r're:^https://www\.tiktok\.com/@zoey.aune',
            'webpage_url': r're:^https://www\.tiktok\.com/@zoey.aune/(video/)?6813765043914624262',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://m.tiktok.com/v/%s.html' % video_id, video_id)

        # The webpage will have a json embedded in a <script id="__NEXT_DATA__"> tag. The JSON holds all the metadata, so fetch that out.
        json_string = self._html_search_regex([r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'],
                                              webpage, 'next_data')
        json_data = self._parse_json(json_string, video_id)
        page_props = json_data['props']['pageProps']

        if page_props.get('statusCode', 0) != 0:
            raise ExtractorError('Video not available', video_id=video_id)

        item_info = page_props['itemInfo']
        item_struct = item_info['itemStruct']
        video_info = item_struct['video']
        video_url = video_info['playAddr']

        # Get extra metadata
        share_info = try_get(item_info, lambda x: x['shareMeta'], dict)
        author_info = try_get(item_struct, lambda x: x['author'], dict)
        stats_info = try_get(item_struct, lambda x: x['stats'], dict)
        height = try_get(video_info, lambda x: x['height'], int)
        width = try_get(video_info, lambda x: x['width'], int)

        thumbnail = video_info.get('cover') or self._og_search_thumbnail(webpage)
        thumbnails = []
        if thumbnail:
            thumbnails.append({
                'url': thumbnail,
                'width': width,
                'height': height
            })

        formats = [{
            'url': video_url,
            'ext': 'mp4',
            'height': height,
            'width': width
        }]

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': str_or_none(share_info.get('desc')),
            'comment_count': int_or_none(stats_info.get('commentCount')),
            'duration': try_get(video_info, lambda x: x['duration'], int),
            'height': height,
            'like_count': int_or_none(stats_info.get('diggCount')),
            'repost_count': int_or_none(stats_info.get('shareCount')),
            'thumbnail': thumbnail,
            'timestamp': try_get(item_struct, lambda x: int(x['createTime']), int),
            'width': width,
            'creator': str_or_none(author_info.get('nickname')),
            'uploader': str_or_none(author_info.get('uniqueId')),
            'uploader_id': str_or_none(author_info.get('id')),
            'uploader_url': 'https://www.tiktok.com/@' + author_info.get('uniqueId'),
            'thumbnails': thumbnails,
            'webpage_url': self._og_search_url(webpage),
            'ext': 'mp4',
            'formats': formats,
            'http_headers': {
                'User-Agent': 'okhttp',
                'Referer': url,
            },
        }

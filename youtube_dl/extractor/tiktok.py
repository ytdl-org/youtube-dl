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
        'md5': 'd679cc9a75bce136e5a2be41fd9f77e0',
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
            'title': 'Zoey on TikTok',
            'upload_date': '20200409',
            'uploader': 'zoey.aune',
            'uploader_id': '6651338645989621765',
            'uploader_url': r're:https://www.tiktok.com/@zoey.aune',
            'webpage_url': r're:https://www.tiktok.com/@zoey.aune/(video/)?6813765043914624262',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://m.tiktok.com/v/%s.html' % video_id, video_id)

        # The webpage will have a json embedded in a <script id="__NEXT_DATA__"> tag. The JSON holds all the metadata, so fetch that out.
        json_string = self._html_search_regex([r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'],
                                              webpage, 'next_data')
        json_data = self._parse_json(json_string, video_id)
        video_data = try_get(json_data, lambda x: x['props']['pageProps'], expected_type=dict)

        # The watermarkless video ID is embedded in the first video file, so we need to download it and get the video ID.
        watermarked_url = video_data['videoData']['itemInfos']['video']['urls'][0]
        watermarked_response = self._download_webpage(watermarked_url, video_id)
        idpos = watermarked_response.index("vid:")
        watermarkless_video_id = watermarked_response[idpos + 4:idpos + 36]
        watermarkless_url = "https://api2-16-h2.musical.ly/aweme/v1/play/?video_id={}&vr_type=0&is_play_url=1&source=PackSourceEnum_PUBLISH&media_type=4".format(watermarkless_video_id)

        # Get extra metadata
        video_info = try_get(video_data, lambda x: x['videoData']['itemInfos'], dict)
        author_info = try_get(video_data, lambda x: x['videoData']['authorInfos'], dict)
        share_info = try_get(video_data, lambda x: x['shareMeta'], dict)
        unique_id = str_or_none(author_info.get('uniqueId'))
        timestamp = try_get(video_info, lambda x: int(x['createTime']), int)
        height = try_get(video_info, lambda x: x['video']['videoMeta']['height'], int)
        width = try_get(video_info, lambda x: x['video']['videoMeta']['width'], int)
        thumbnails = []
        thumbnails.append({
            'url': video_info.get('thumbnail') or self._og_search_thumbnail(webpage),
            'width': width,
            'height': height
        })

        formats = []
        formats.append({
            'url': watermarkless_url,
            'ext': 'mp4',
            'height': height,
            'width': width
        })

        if video_data.get('statusCode') != 0:
            raise ExtractorError('Video not available', video_id=video_id)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': str_or_none(video_info.get('text')) or str_or_none(share_info.get('desc')),
            'comment_count': int_or_none(video_info.get('commentCount')),
            'duration': try_get(video_info, lambda x: x['video']['videoMeta']['duration'], int),
            'height': height,
            'like_count': int_or_none(video_info.get('diggCount')),
            'repost_count': int_or_none(video_info.get('shareCount')),
            'thumbnail': try_get(video_info, lambda x: x['covers'][0], str),
            'timestamp': timestamp,
            'width': width,
            'creator': str_or_none(author_info.get('nickName')),
            'uploader': unique_id,
            'uploader_id': str_or_none(author_info.get('userId')),
            'uploader_url': 'https://www.tiktok.com/@' + unique_id,
            'thumbnails': thumbnails,
            'webpage_url': self._og_search_url(webpage),
            'ext': 'mp4',
            'formats': formats,
            'http_headers': {
                'User-Agent': 'okhttp',
            }
        }

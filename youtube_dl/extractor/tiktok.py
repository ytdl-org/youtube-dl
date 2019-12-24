# coding: utf-8
from __future__ import unicode_literals
from datetime import datetime
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    try_get
)


class TikTokBaseIE(InfoExtractor):
    def _video_info(self, video_info):
        return {
            'id': str_or_none(video_info.get('id')),
            'thumbnail': try_get(video_info, lambda x: x['covers'][0], str) or try_get(video_info, lambda x: x['video']['videoMeta']['cover'][0], str),
            'video_url': try_get(video_info, lambda x: x['video']['urls'][0], str) or video_info.get('video', {}).get('urls', [None])[0],
            'width': try_get(video_info, lambda x: x['video']['videoMeta']['width'], int) or try_get(video_info, lambda x: x['width'], int),
            'height': try_get(video_info, lambda x: x['video']['videoMeta']['height'], int) or try_get(video_info, lambda x: x['height'], int),
            'duration': try_get(video_info, lambda x: x['video']['videoMeta']['duration'], int),
            'description': str_or_none(video_info.get('text')),
            'comment_count': int_or_none(video_info.get('commentCount')),
            'like_count': int_or_none(video_info.get('diggCount')),
            'repost_count': int_or_none(video_info.get('shareCount')),
            'timestamp': str_or_none(video_info.get('createTime')),
            'track_id': str_or_none(video_info.get('musicId'))
        }

    def _author_info(self, author_info):
        return {
            'uploader': str_or_none(author_info.get('uniqueId')),
            'creator': str_or_none(author_info.get('nickName')),
            'uploader_id': str_or_none(author_info.get('userId')),
            'channel_id': str_or_none(author_info.get('userId'))
        }

    def _track_info(self, track_info):
        return {
            'track': str_or_none(track_info.get('musicName')),
            'track_id': str_or_none(track_info.get('musicId')),
            'artist': str_or_none(track_info.get('authorName'))
        }

    def _share_info(self, share_info):
        return {
            'title': str_or_none(share_info.get('title')),
            'description': str_or_none(share_info.get('desc')),
            'image': try_get(share_info, lambda x: x['image'], dict),
            'width': try_get(share_info, lambda x: x['image']['width'], int),
            'height': try_get(share_info, lambda x: x['image']['height'], int),
        }

    def _extract_aweme(self, video_data, webpage):
        video_info_data = try_get(
            video_data, lambda x: x['videoData']['itemInfos'], dict)
        author_info_data = try_get(
            video_data, lambda x: x['videoData']['authorInfos'], dict)
        track_info_data = try_get(
            video_data, lambda x: x['videoData']['musicInfos'], dict)
        share_info_data = try_get(video_data, lambda x: x['shareMeta'], dict)

        video_info = self._video_info(video_info_data)
        author_info = self._author_info(author_info_data)
        track_info = self._track_info(track_info_data)
        share_info = self._share_info(share_info_data)

        timestamp = int(video_info.get('timestamp')) or 0
        date = str_or_none(datetime.fromtimestamp(
            timestamp).strftime('%Y%m%d'))

        thumbnails = []
        thumbnails.append({
            'url': video_info.get('thumbnail') or self._og_search_thumbnail(webpage),
            'width': video_info.get('width'),
            'height': video_info.get('height')
        })

        description = video_info.get(
            'description') or share_info.get('description')
        if description is None:
            tags = []
        else:
            tags = re.findall(r"#(\w+)", description)

        formats = []
        formats.append({
            'url': video_info.get('video_url') or self._og_search_video_url(webpage),
            'ext': 'mp4',
            'height': video_info.get('height'),
            'width': video_info.get('width'),
        })

        return {
            'artist': track_info.get('artist'),
            'channel_id': author_info.get('channel_id'),
            'channel_url': 'https://www.tiktok.com/@{}'.format(author_info.get('uploader')),
            'comment_count': video_info.get('comment_count'),
            'creator': author_info.get('creator'),
            'description': description,
            'duration': video_info.get('duration'),
            'formats': formats,
            'height': video_info.get('height'),
            'id': video_info.get('id'),
            'like_count': video_info.get('like_count'),
            'playlist_title': share_info.get('title'),
            'playlist_uploader': author_info.get('uploader'),
            'playlist_uploader_id': author_info.get('uploader_id'),
            'repost_count': video_info.get('repost_count'),
            'release_date': date,
            'tags': tags,
            'thumbnail': video_info.get('thumbnail'),
            'thumbnails': thumbnails,
            'timestamp': int(video_info.get('timestamp')),
            'title': share_info.get('title') or self._og_search_title(webpage),
            'track': track_info.get('track'),
            'track_id': track_info.get('track_id'),
            'upload_date': date,
            'uploader': author_info.get('uploader'),
            'uploader_id': author_info.get('uploader_id'),
            'uploader_url': 'https://www.tiktok.com/@{}'.format(author_info.get('uploader')),
            'webpage_url': self._og_search_url(webpage),
            'width': video_info.get('width')
        }


class TikTokIE(TikTokBaseIE):
    _VALID_URL = r'''(?x)
                 https?://
                 (?:
                    (?:www|m)\.
                    (?:tiktok.com)\/
                    (@(?P<username>[\w\.]+))?
                    (?:v|video|embed|trending)?(?:\/)?
                    (?:video)?(?:\/)?
                    (?:\?shareId=)?
                 )
                 (?P<id>[\d]{6,})
                 (?:\.html)?
                 (?:\?.*)?
                 $
                 '''

    _TESTS = [{
        'url': 'https://www.tiktok.com/@leenabhushan/video/6748451240264420610',
        'md5': '34a7543afd5a151b0840ba6736fb633b',
        'info_dict': {
            'id': '6748451240264420610',
            'ext': 'mp4',
            'title': 'facestoriesbyleenabh on TikTok',
            'description': 'md5:a9f6c0c44a1ff2249cae610372d0ae95',
            'thumbnail': r're:^https?://[\w\/\.\-]+(~[\w\-]+\.image)?',
            'uploader': 'leenabhushan',
            'timestamp': 1571246252,
            'upload_date': '20191016',
            'comment_count': int,
            'repost_count': int,
            'like_count': int,
            'playlist_title': 'facestoriesbyleenabh on TikTok',
            'playlist_uploader': 'leenabhushan',
            'playlist_uploader_id': '6691488002098119685',
            'artist': 'Jass Manak',
            'channel_id': '6691488002098119685',
            'channel_url': 'https://www.tiktok.com/@leenabhushan',
            'creator': 'facestoriesbyleenabh',
            'duration': 13,
            'formats': list,
            'height': 1280,
            'release_date': '20191016',
            'tags': list,
            'thumbnails': list,
            'track': 'Lehanga',
            'track_id': '6716465478027447045',
            'uploader_id': '6691488002098119685',
            'uploader_url': r're:https://www.tiktok.com/@leenabhushan',
            'webpage_url': r're:https://www.tiktok.com/@leenabhushan/(video/)?6748451240264420610',
            'width': 720,
        }
    }, {
        'url': 'https://www.tiktok.com/@patroxofficial/video/6742501081818877190?langCountry=en',
        'md5': '06b9800d47d5fe51a19e322dd86e61c9',
        'info_dict': {
            'artist': 'Evan Todd, Jessica Keenan Wynn, Alice Lee, Barrett Wilbert Weed & Jon Eidson',
            'channel_id': '18702747',
            'channel_url': 'https://www.tiktok.com/@patroxofficial',
            'comment_count': int,
            'creator': 'patroX',
            'description': 'md5:5e2a23877420bb85ce6521dbee39ba94',
            'duration': 27,
            'ext': 'mp4',
            'formats': list,
            'height': 960,
            'id': '6742501081818877190',
            'like_count': int,
            'playlist_title': 'patroX on TikTok',
            'playlist_uploader_id': '18702747',
            'playlist_uploader': 'patroxofficial',
            'release_date': '20190930',
            'repost_count': int,
            'tags': list,
            'thumbnail': r're:^https?://[\w\/\.\-]+(~[\w\-]+\.image)?',
            'thumbnails': list,
            'timestamp': 1569860870,
            'title': 'patroX on TikTok',
            'track_id': '209649576000286720',
            'track': 'Big Fun',
            'upload_date': '20190930',
            'uploader_id': '18702747',
            'uploader_url': r're:https://www.tiktok.com/@patroxofficial',
            'uploader': 'patroxofficial',
            'webpage_url': r're:https://www.tiktok.com/@patroxofficial/(video/)?6742501081818877190',
            'width': 540,
        }
    }, {
        'url': 'https://m.tiktok.com/v/6749869095467945218.html',
        'only_matching': True
    }, {
        'url': 'https://www.tiktok.com/@cchelseameow/video/6751181801206729990',
        'only_matching': True
    }, {
        'url': 'https://www.tiktok.com/embed/6567659045795758085',
        'only_matching': True
    }, {
        'url': 'https://www.tiktok.com/trending?shareId=6744531482393545985',
        'only_matching': True
    }, {
        'url': 'https://www.tiktok.com/@leenabhushan/video/6748451240264420610?enter_from=h5_m',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Referer': url
        }
        webpage = self._download_webpage(url, video_id, headers=headers, note='Downloading video webpage')
        json_string = self._search_regex(
            r'id=\"__NEXT_DATA__\"\s+type=\"application\/json\">\s*(?P<json_string>[^<]+)',
            webpage, 'json_string', group='json_string')
        json_data = self._parse_json(json_string, video_id)
        video_data = try_get(json_data, lambda x: x['props']['pageProps'], expected_type=dict)

        # Chech statusCode for success
        if video_data.get('statusCode') == 0:
            return self._extract_aweme(video_data, webpage)

        raise ExtractorError("Video not available", video_id=video_id)


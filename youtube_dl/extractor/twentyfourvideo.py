# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    int_or_none,
)


class TwentyFourVideoIE(InfoExtractor):
    IE_NAME = '24video'
    _VALID_URL = r'https?://(?:www\.)?24video\.net/(?:video/(?:view|xml)/|player/new24_play\.swf\?id=)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'http://www.24video.net/video/view/1044982',
            'md5': '48dd7646775690a80447a8dca6a2df76',
            'info_dict': {
                'id': '1044982',
                'ext': 'mp4',
                'title': 'Эротика каменного века',
                'description': 'Как смотрели порно в каменном веке.',
                'thumbnail': 're:^https?://.*\.jpg$',
                'uploader': 'SUPERTELO',
                'duration': 31,
                'timestamp': 1275937857,
                'upload_date': '20100607',
                'age_limit': 18,
                'like_count': int,
                'dislike_count': int,
            },
        },
        {
            'url': 'http://www.24video.net/player/new24_play.swf?id=1044982',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.24video.net/video/view/%s' % video_id, video_id)

        title = self._og_search_title(webpage)
        description = self._html_search_regex(
            r'<span itemprop="description">([^<]+)</span>', webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        duration = int_or_none(self._og_search_property(
            'duration', webpage, 'duration', fatal=False))
        timestamp = parse_iso8601(self._search_regex(
            r'<time id="video-timeago" datetime="([^"]+)" itemprop="uploadDate">',
            webpage, 'upload date'))

        uploader = self._html_search_regex(
            r'Загрузил\s*<a href="/jsecUser/movies/[^"]+" class="link">([^<]+)</a>',
            webpage, 'uploader', fatal=False)

        view_count = int_or_none(self._html_search_regex(
            r'<span class="video-views">(\d+) просмотр',
            webpage, 'view count', fatal=False))
        comment_count = int_or_none(self._html_search_regex(
            r'<div class="comments-title" id="comments-count">(\d+) комментари',
            webpage, 'comment count', fatal=False))

        formats = []

        pc_video = self._download_xml(
            'http://www.24video.net/video/xml/%s?mode=play' % video_id,
            video_id, 'Downloading PC video URL').find('.//video')

        formats.append({
            'url': pc_video.attrib['url'],
            'format_id': 'pc',
            'quality': 1,
        })

        like_count = int_or_none(pc_video.get('ratingPlus'))
        dislike_count = int_or_none(pc_video.get('ratingMinus'))
        age_limit = 18 if pc_video.get('adult') == 'true' else 0

        mobile_video = self._download_xml(
            'http://www.24video.net/video/xml/%s' % video_id,
            video_id, 'Downloading mobile video URL').find('.//video')

        formats.append({
            'url': mobile_video.attrib['url'],
            'format_id': 'mobile',
            'quality': 0,
        })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': duration,
            'timestamp': timestamp,
            'view_count': view_count,
            'comment_count': comment_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'age_limit': age_limit,
            'formats': formats,
        }

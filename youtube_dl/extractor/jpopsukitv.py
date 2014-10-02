# coding=utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class JpopsukiIE(InfoExtractor):
    IE_NAME = 'jpopsuki.tv'
    _VALID_URL = r'https?://(?:www\.)?jpopsuki\.tv/(?:category/)?video/[^/]+/(?P<id>\S+)'

    _TEST = {
        'url': 'http://www.jpopsuki.tv/video/ayumi-hamasaki---evolution/00be659d23b0b40508169cdee4545771',
        'md5': '88018c0c1a9b1387940e90ec9e7e198e',
        'info_dict': {
            'id': '00be659d23b0b40508169cdee4545771',
            'ext': 'mp4',
            'title': 'ayumi hamasaki - evolution',
            'description': 'Release date: 2001.01.31\r\n浜崎あゆみ - evolution',
            'thumbnail': 'http://www.jpopsuki.tv/cache/89722c74d2a2ebe58bcac65321c115b2.jpg',
            'uploader': 'plama_chan',
            'uploader_id': '404',
            'upload_date': '20121101'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = 'http://www.jpopsuki.tv' + self._html_search_regex(
            r'<source src="(.*?)" type', webpage, 'video url')

        video_title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        uploader = self._html_search_regex(
            r'<li>from: <a href="/user/view/user/(.*?)/uid/',
            webpage, 'video uploader', fatal=False)
        uploader_id = self._html_search_regex(
            r'<li>from: <a href="/user/view/user/\S*?/uid/(\d*)',
            webpage, 'video uploader_id', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            r'<li>uploaded: (.*?)</li>', webpage, 'video upload_date',
            fatal=False))
        view_count_str = self._html_search_regex(
            r'<li>Hits: ([0-9]+?)</li>', webpage, 'video view_count',
            fatal=False)
        comment_count_str = self._html_search_regex(
            r'<h2>([0-9]+?) comments</h2>', webpage, 'video comment_count',
            fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'view_count': int_or_none(view_count_str),
            'comment_count': int_or_none(comment_count_str),
        }

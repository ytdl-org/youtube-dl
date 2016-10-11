# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    sanitized_Request,
)


class YuvutuIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?yuvutu.com/video/(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.yuvutu.com/video/330/',
        'md5': 'af4a0d2eabec6b6bd43cd6b68543fa9c',
        'info_dict': {
            'id': '330',
            'title': 'carnal bliss',
            'ext': 'flv',
            'age_limit': 18,
            'thumbnail': 're:https?://.*?\.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r"class=[\"']video-title-content[\"']>.+?>(.+?)<", webpage, 'title')
        thumbnail_url = self._html_search_regex(
            r"itemprop=[\"']thumbnailURL[\"']\s+content=[\"'](.+?)[\"']", webpage, 'thumbnail')

        embed_url = self._html_search_regex(
            r"[\"'](\/embed_video\.php.+?)[\"']", webpage, 'embed')
        embed_webpage = self._download_webpage(
            "http://www.yuvutu.com/" + embed_url, video_id)
        video_url = self._html_search_regex(
            r"file:\s*[\"']([^\s]+)[\"']", embed_webpage, 'video_url')

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail_url,
            'ext': determine_ext(video_url, 'mp4'),
            'title': title,
            'age_limit': 18,
        }


class YuvutuUserIE(InfoExtractor):
    IE_DESC = 'Yuvutu user profile'
    _VALID_URL = r'http://(?:www\.)?yuvutu\.com/modules\.php\?name=YuPeople&action=view_videos&user_id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.yuvutu.com/modules.php?name=YuPeople&action=view_videos&user_id=1072966',
        'info_dict': {
            'id': '1072966',
            'age_limit': 18,
        },
        'playlist_mincount': 90,
    }

    def _real_extract(self, url):
        user_id = self._match_id(url)

        entries = []
        for pagenum in itertools.count(1):
            request = sanitized_Request(
                'http://www.yuvutu.com/modules.php?name=YuPeople&action=view_videos&user_id=%s&page=%d' % (user_id, pagenum))
            page = self._download_webpage(request, user_id, 'Downloading user page %d' % pagenum)

            video_ids = re.findall(
                r'class=[\'"]thumb-image[\'"]>\s+<a\s+href=[\'"]/video/([^/]+)', page)
            if not video_ids:
                break
            for video_id in video_ids:
                entries.append(self.url_result('http://www.yuvutu.com/video/%s/' % video_id, YuvutuIE.ie_key()))

        playlist = self.playlist_result(entries, user_id)
        playlist['age_limit'] = 18
        return playlist

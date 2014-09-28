# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate
)


class THVideoIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?thvideo\.tv/(?:v/th|mobile\.php\?cid=)(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://thvideo.tv/v/th1987/',
        'md5': 'fa107b1f73817e325e9433505a70db50',
        'info_dict': {
            'id': '1987',
            'ext': 'mp4',
            'title': '【动画】秘封活动记录 ～ The Sealed Esoteric History.分镜稿预览',
            'display_id': 'th1987',
            'thumbnail': 'http://thvideo.tv/uploadfile/2014/0722/20140722013459856.jpg',
            'description': '社团京都幻想剧团的第一个东方二次同人动画作品「秘封活动记录 ～ The Sealed Esoteric History.」 本视频是该动画第一期的分镜草稿...',
            'upload_date': '20140722'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # extract download link from mobile player page
        webpage_player = self._download_webpage(
            'http://thvideo.tv/mobile.php?cid=%s-0' % (video_id),
            video_id, note='Downloading video source page')
        video_url = self._html_search_regex(
            r'<source src="(.*?)" type', webpage_player, 'video url')

        # extract video info from main page
        webpage = self._download_webpage(
            'http://thvideo.tv/v/th%s' % (video_id), video_id)
        title = self._og_search_title(webpage)
        display_id = 'th%s' % video_id
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        upload_date = unified_strdate(self._html_search_regex(
            r'span itemprop="datePublished" content="(.*?)">', webpage,
            'upload date', fatal=False))

        return {
            'id': video_id,
            'ext': 'mp4',
            'url': video_url,
            'title': title,
            'display_id': display_id,
            'thumbnail': thumbnail,
            'description': description,
            'upload_date': upload_date
        }


class THVideoPlaylistIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?thvideo\.tv/mylist(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://thvideo.tv/mylist2',
        'info_dict': {
            'id': '2',
            'title': '幻想万華鏡',
        },
        'playlist_mincount': 23,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)
        list_title = self._html_search_regex(
            r'<h1 class="show_title">(.*?)<b id', webpage, 'playlist title',
            fatal=False)

        entries = [
            self.url_result('http://thvideo.tv/v/th' + id, 'THVideo')
            for id in re.findall(r'<dd><a href="http://thvideo.tv/v/th(\d+)/" target=', webpage)]

        return self.playlist_result(entries, playlist_id, list_title)

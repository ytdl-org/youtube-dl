# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
)


class KontrTubeIE(InfoExtractor):
    IE_NAME = 'kontrtube'
    IE_DESC = 'KontrTube.ru - Труба зовёт'
    _VALID_URL = r'https?://(?:www\.)?kontrtube\.ru/videos/(?P<id>\d+)/(?P<display_id>[^/]+)/'

    _TEST = {
        'url': 'http://www.kontrtube.ru/videos/2678/nad-olimpiyskoy-derevney-v-sochi-podnyat-rossiyskiy-flag/',
        'md5': '975a991a4926c9a85f383a736a2e6b80',
        'info_dict': {
            'id': '2678',
            'display_id': 'nad-olimpiyskoy-derevney-v-sochi-podnyat-rossiyskiy-flag',
            'ext': 'mp4',
            'title': 'Над олимпийской деревней в Сочи поднят российский флаг',
            'description': 'md5:80edc4c613d5887ae8ccf1d59432be41',
            'thumbnail': 'http://www.kontrtube.ru/contents/videos_screenshots/2000/2678/preview.mp4.jpg',
            'duration': 270,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(
            url, display_id, 'Downloading page')

        video_url = self._search_regex(
            r"video_url\s*:\s*'(.+?)/?',", webpage, 'video URL')
        thumbnail = self._search_regex(
            r"preview_url\s*:\s*'(.+?)/?',", webpage, 'thumbnail', fatal=False)
        title = self._html_search_regex(
            r'(?s)<h2>(.+?)</h2>', webpage, 'title')
        description = self._html_search_meta(
            'description', webpage, 'description')

        duration = self._search_regex(
            r'Длительность: <em>([^<]+)</em>', webpage, 'duration', fatal=False)
        if duration:
            duration = parse_duration(duration.replace('мин', 'min').replace('сек', 'sec'))

        view_count = self._search_regex(
            r'Просмотров: <em>([^<]+)</em>',
            webpage, 'view count', fatal=False)
        if view_count:
            view_count = int_or_none(view_count.replace(' ', ''))

        comment_count = int_or_none(self._search_regex(
            r'Комментарии \((\d+)\)<', webpage, ' comment count', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'comment_count': int_or_none(comment_count),
        }

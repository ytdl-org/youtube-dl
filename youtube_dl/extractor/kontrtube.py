# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class KontrTubeIE(InfoExtractor):
    IE_NAME = 'kontrtube'
    IE_DESC = 'KontrTube.ru - Труба зовёт'
    _VALID_URL = r'http://(?:www\.)?kontrtube\.ru/videos/(?P<id>\d+)/.+'

    _TEST = {
        'url': 'http://www.kontrtube.ru/videos/2678/nad-olimpiyskoy-derevney-v-sochi-podnyat-rossiyskiy-flag/',
        'md5': '975a991a4926c9a85f383a736a2e6b80',
        'info_dict': {
            'id': '2678',
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

        webpage = self._download_webpage(url, video_id, 'Downloading page')

        video_url = self._html_search_regex(r"video_url: '(.+?)/?',", webpage, 'video URL')
        thumbnail = self._html_search_regex(r"preview_url: '(.+?)/?',", webpage, 'video thumbnail', fatal=False)
        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'video title')
        description = self._html_search_meta('description', webpage, 'video description')

        mobj = re.search(
            r'<div class="col_2">Длительность: <span>(?P<minutes>\d+)м:(?P<seconds>\d+)с</span></div>', webpage)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        view_count = self._html_search_regex(
            r'<div class="col_2">Просмотров: <span>(\d+)</span></div>', webpage, 'view count', fatal=False)

        comment_count = None
        comment_str = self._html_search_regex(
            r'Комментарии: <span>([^<]+)</span>', webpage, 'comment count', fatal=False)
        if comment_str.startswith('комментариев нет'):
            comment_count = 0
        else:
            mobj = re.search(r'\d+ из (?P<total>\d+) комментариев', comment_str)
            if mobj:
                comment_count = mobj.group('total')

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'comment_count': int_or_none(comment_count),
        }

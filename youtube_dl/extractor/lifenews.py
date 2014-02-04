# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class LifeNewsIE(InfoExtractor):
    IE_NAME = 'lifenews'
    IE_DESC = 'LIFE | NEWS'
    _VALID_URL = r'http://lifenews\.ru/(?:mobile/)?news/(?P<id>\d+)'
    
    _TEST = {
        'url': 'http://lifenews.ru/news/126342',
        'file': '126342.mp4',
        'md5': 'e1b50a5c5fb98a6a544250f2e0db570a',
        'info_dict': {
            'title': 'МВД разыскивает мужчин, оставивших в IKEA сумку с автоматом',
            'description': 'Камеры наблюдения гипермаркета зафиксировали троих мужчин, спрятавших оружейный арсенал в камере хранения.',
            'thumbnail': 'http://lifenews.ru/static/posts/2014/1/126342/.video.jpg',
            'upload_date': '20140130',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage('http://lifenews.ru/mobile/news/%s' % video_id, video_id, 'Downloading page')

        video_url = self._html_search_regex(
            r'<video.*?src="([^"]+)".*?></video>', webpage, 'video URL')
        
        thumbnail = self._html_search_regex(
            r'<video.*?poster="([^"]+)".*?"></video>', webpage, 'video thumbnail')

        title = self._og_search_title(webpage)
        TITLE_SUFFIX = ' - Первый по срочным новостям — LIFE | NEWS'
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)]

        description = self._og_search_description(webpage)

        view_count = self._html_search_regex(
            r'<div class=\'views\'>(\d+)</div>', webpage, 'view count')
        comment_count = self._html_search_regex(
            r'<div class=\'comments\'>(\d+)</div>', webpage, 'comment count')

        upload_date = self._html_search_regex(
            r'<time datetime=\'([^\']+)\'>', webpage, 'upload date')

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'view_count': view_count,
            'comment_count': comment_count,
            'upload_date': unified_strdate(upload_date),
        }
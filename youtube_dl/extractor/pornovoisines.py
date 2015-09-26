# coding: utf-8
from __future__ import unicode_literals

import re
import random

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
    unified_strdate,
)


class PornoVoisinesIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?pornovoisines\.com/showvideo/(?P<id>\d+)/(?P<display_id>[^/]+)'

    _VIDEO_URL_TEMPLATE = 'http://stream%d.pornovoisines.com' \
        '/static/media/video/transcoded/%s-640x360-1000-trscded.mp4'

    _SERVER_NUMBERS = (1, 2)

    _TEST = {
        'url': 'http://www.pornovoisines.com/showvideo/1285/recherche-appartement/',
        'md5': '5ac670803bc12e9e7f9f662ce64cf1d1',
        'info_dict': {
            'id': '1285',
            'display_id': 'recherche-appartement',
            'ext': 'mp4',
            'title': 'Recherche appartement',
            'description': 'md5:819ea0b785e2a04667a1a01cdc89594e',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20140925',
            'duration': 120,
            'view_count': int,
            'average_rating': float,
            'categories': ['Débutantes', 'Scénario', 'Sodomie'],
            'age_limit': 18,
        }
    }

    @classmethod
    def build_video_url(cls, num):
        return cls._VIDEO_URL_TEMPLATE % (random.choice(cls._SERVER_NUMBERS), num)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, video_id)

        video_url = self.build_video_url(video_id)

        title = self._html_search_regex(
            r'<h1>(.+?)</h1>', webpage, 'title', flags=re.DOTALL)
        description = self._html_search_regex(
            r'<article id="descriptif">(.+?)</article>',
            webpage, "description", fatal=False, flags=re.DOTALL)

        thumbnail = self._search_regex(
            r'<div id="mediaspace%s">\s*<img src="/?([^"]+)"' % video_id,
            webpage, 'thumbnail', fatal=False)
        if thumbnail:
            thumbnail = 'http://www.pornovoisines.com/%s' % thumbnail

        upload_date = unified_strdate(self._search_regex(
            r'Publié le ([\d-]+)', webpage, 'upload date', fatal=False))
        duration = int_or_none(self._search_regex(
            'Durée (\d+)', webpage, 'duration', fatal=False))
        view_count = int_or_none(self._search_regex(
            r'(\d+) vues', webpage, 'view count', fatal=False))
        average_rating = self._search_regex(
            r'Note\s*:\s*(\d+(?:,\d+)?)', webpage, 'average rating', fatal=False)
        if average_rating:
            average_rating = float_or_none(average_rating.replace(',', '.'))

        categories = self._html_search_meta(
            'keywords', webpage, 'categories', fatal=False)
        if categories:
            categories = [category.strip() for category in categories.split(',')]

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'average_rating': average_rating,
            'categories': categories,
            'age_limit': 18,
        }

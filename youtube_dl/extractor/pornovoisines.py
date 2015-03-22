# coding: utf-8
from __future__ import unicode_literals

import re
import datetime
import random

from ..compat import compat_urllib_parse
from .common import InfoExtractor

class PornoVoisinesIE(InfoExtractor):
    _VALID_URL = r'^((?:http://)?(?:www\.)?pornovoisines.com)/showvideo/(\d+)/([^/]+)'

    VIDEO_URL_TEMPLATE = 'http://stream%d.pornovoisines.com' \
        '/static/media/video/transcoded/%s-640x360-1000-trscded.mp4'

    SERVER_NUMBERS = (1, 2)

    _TEST = {
        'url': 'http://www.pornovoisines.com/showvideo/1285/recherche-appartement/',
        'md5': '5ac670803bc12e9e7f9f662ce64cf1d1',
        'info_dict': {
            'id': '1285',
            'display_id': 'recherche-appartement',
            'ext': 'mp4',
            'title': "Recherche appartement",
            'upload_date': '20140925',
            'view_count': int,
            'duration': 120,
            'categories': ["Débutante", "Scénario", "Sodomie"],
            'description': 're:^Pour la .+ original...$',
            'thumbnail': 're:^http://',
            'uploader': "JMTV",
            'average_rating': float,
            'comment_count': int,
            'age_limit': 18,
        }
    }

    @classmethod
    def build_video_url(cls, id):
        server_nr = random.choice(cls.SERVER_NUMBERS)
        return cls.VIDEO_URL_TEMPLATE % (server_nr, id)

    @staticmethod
    def parse_upload_date(str):
        return datetime.datetime.strptime(str, "%d-%m-%Y").strftime("%Y%m%d")

    @staticmethod
    def parse_categories(str):
        return map(lambda s: s.strip(), str.split(','))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url_prefix = mobj.group(1)
        id = mobj.group(2)
        display_id = mobj.group(3)

        webpage = self._download_webpage(url, id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title',
            flags=re.DOTALL)
        url = self.build_video_url(id)
        upload_date = self.parse_upload_date(
            self._search_regex(r'Publié le (\d\d-\d\d-\d{4})', webpage,
            'upload date'))
        view_count = int(self._search_regex(r'(\d+) vues', webpage, 'view count'))
        duration = int(self._search_regex('Durée (\d+)', webpage, 'duration'))
        categories = self.parse_categories(self._html_search_regex(
            r'<li class="categorie">(.+?)</li>', webpage, "categories",
            flags=re.DOTALL))
        description = self._html_search_regex(
            r'<article id="descriptif">(.+?)</article>', webpage, "description",
            flags=re.DOTALL)
        thumbnail = url_prefix + self._html_search_regex(re.compile(
            '<div id="mediaspace' + id + '">.*?<img src="(.+?)"', re.DOTALL),
            webpage, "thumbnail")
        uploader = re.sub(r' *\| *$', '',
            self._html_search_regex(r'<li class="auteur">(.+?)</li>', webpage,
            "uploader", flags=re.DOTALL))
        average_rating = float(self._search_regex(r'Note : (\d+,\d+)',
            webpage, "average rating").replace(',', '.'))
        comment_count = int(self._search_regex(r'\((\d+)\)', webpage,
            "comment count"))

        return {
            'id': id,
            'display_id': display_id,
            'url': url,
            'title': title,
            'upload_date': upload_date,
            'view_count': view_count,
            'duration': duration,
            'categories': categories,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'average_rating': average_rating,
            'comment_count': comment_count,
            'age_limit': 18,
        }

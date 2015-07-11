# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    url_basename,
)


class RDScaIE(InfoExtractor):
    IE_NAME = 'RDS.ca'
    _VALID_URL = r'http://(?:www\.)?rds\.ca/videos/(?P<id>.*)'

    _TESTS = [{
        'url': 'http://www.rds.ca/videos/football/nfl/fowler-jr-prend-la-direction-de-jacksonville-3.1132799',
        'info_dict': {
            "ext": "mp4",
            "title": "Fowler Jr. prend la direction de Jacksonville",
            "description": "Dante Fowler Jr. est le troisième choix du repêchage 2015 de la NFL. ",
            "timestamp": 1430397346,
        }
    }]

    def _real_extract(self, url):
        video_id = url_basename(url)

        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(
            r'<span itemprop="name"[^>]*>([^\n]*)</span>', webpage, 'video title', default=None)
        video_url = self._search_regex(
            r'<span itemprop="contentURL" content="([^"]+)"', webpage, 'video URL')
        upload_date = parse_iso8601(self._search_regex(
            r'<span itemprop="uploadDate" content="([^"]+)"', webpage, 'upload date', default=None))
        description = self._search_regex(
            r'<span itemprop="description"[^>]*>([^\n]*)</span>', webpage, 'description', default=None)
        thumbnail = self._search_regex(
            r'<span itemprop="thumbnailUrl" content="([^"]+)"', webpage, 'upload date', default=None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': upload_date,
            'formats': [{
                'url': video_url,
            }],
        }

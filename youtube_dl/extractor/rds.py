# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class RDSIE(InfoExtractor):
    IE_DESC = 'RDS.ca'
    _VALID_URL = r'https?://(?:www\.)?rds\.ca/vid(?:[eé]|%C3%A9)os/(?:[^/]+/)*(?P<display_id>[^/]+)-(?P<id>\d+\.\d+)'

    _TESTS = [{
        'url': 'http://www.rds.ca/videos/football/nfl/fowler-jr-prend-la-direction-de-jacksonville-3.1132799',
        'info_dict': {
            'id': '3.1132799',
            'display_id': 'fowler-jr-prend-la-direction-de-jacksonville',
            'ext': 'mp4',
            'title': 'Fowler Jr. prend la direction de Jacksonville',
            'description': 'Dante Fowler Jr. est le troisième choix du repêchage 2015 de la NFL. ',
            'timestamp': 1430397346,
            'upload_date': '20150430',
            'duration': 154.354,
            'age_limit': 0,
        }
    }, {
        'url': 'http://www.rds.ca/vid%C3%A9os/un-voyage-positif-3.877934',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        # TODO: extract f4m from 9c9media.com
        video_url = self._search_regex(
            r'<span[^>]+itemprop="contentURL"[^>]+content="([^"]+)"',
            webpage, 'video url')

        title = self._og_search_title(webpage) or self._html_search_meta(
            'title', webpage, 'title', fatal=True)
        description = self._og_search_description(webpage) or self._html_search_meta(
            'description', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage) or self._search_regex(
            [r'<link[^>]+itemprop="thumbnailUrl"[^>]+href="([^"]+)"',
             r'<span[^>]+itemprop="thumbnailUrl"[^>]+content="([^"]+)"'],
            webpage, 'thumbnail', fatal=False)
        timestamp = parse_iso8601(self._search_regex(
            r'<span[^>]+itemprop="uploadDate"[^>]+content="([^"]+)"',
            webpage, 'upload date', fatal=False))
        duration = parse_duration(self._search_regex(
            r'<span[^>]+itemprop="duration"[^>]+content="([^"]+)"',
            webpage, 'duration', fatal=False))
        age_limit = self._family_friendly_search(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'age_limit': age_limit,
        }

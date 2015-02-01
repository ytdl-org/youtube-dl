# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
)


class TouTvIE(InfoExtractor):
    IE_NAME = 'tou.tv'
    _VALID_URL = r'https?://www\.tou\.tv/(?P<id>[a-zA-Z0-9_-]+(?:/(?P<episode>S[0-9]+E[0-9]+)))'

    _TEST = {
        'url': 'http://www.tou.tv/30-vies/S04E41',
        'info_dict': {
            'id': '30-vies_S04E41',
            'ext': 'mp4',
            'title': '30 vies Saison 4 / Épisode 41',
            'description': 'md5:da363002db82ccbe4dafeb9cab039b09',
            'age_limit': 8,
            'uploader': 'Groupe des Nouveaux Médias',
            'duration': 1296,
            'upload_date': '20131118',
            'thumbnail': 'http://static.tou.tv/medias/images/2013-11-18_19_00_00_30VIES_0341_01_L.jpeg',
        },
        'params': {
            'skip_download': True,  # Requires rtmpdump
        },
        'skip': 'Only available in Canada'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        mediaId = self._search_regex(
            r'"idMedia":\s*"([^"]+)"', webpage, 'media ID')

        streams_url = 'http://release.theplatform.com/content.select?pid=' + mediaId
        streams_doc = self._download_xml(
            streams_url, video_id, note='Downloading stream list')

        video_url = next(n.text
                         for n in streams_doc.findall('.//choice/url')
                         if '//ad.doubleclick' not in n.text)
        if video_url.endswith('/Unavailable.flv'):
            raise ExtractorError(
                'Access to this video is blocked from outside of Canada',
                expected=True)

        duration_str = self._html_search_meta(
            'video:duration', webpage, 'duration')
        duration = int(duration_str) if duration_str else None
        upload_date_str = self._html_search_meta(
            'video:release_date', webpage, 'upload date')
        upload_date = unified_strdate(upload_date_str) if upload_date_str else None

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': video_url,
            'description': self._og_search_description(webpage),
            'uploader': self._dc_search_uploader(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'age_limit': self._media_rating_search(webpage),
            'duration': duration,
            'upload_date': upload_date,
            'ext': 'mp4',
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_age_limit,
    parse_iso8601,
    smuggle_url,
)


class TenPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?10play\.com\.au/[^/]+/episodes/[^/]+/[^/]+/(?P<id>tpv\d{6}[a-z]{5})'
    _TEST = {
        'url': 'https://10play.com.au/masterchef/episodes/season-1/masterchef-s1-ep-1/tpv190718kwzga',
        'info_dict': {
            'id': '6060533435001',
            'ext': 'mp4',
            'title': 'MasterChef - S1 Ep. 1',
            'description': 'md5:4fe7b78e28af8f2d900cd20d900ef95c',
            'age_limit': 10,
            'timestamp': 1240828200,
            'upload_date': '20090427',
            'uploader_id': '2199827728001',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        }
    }
    BRIGHTCOVE_URL_TEMPLATE = 'https://players.brightcove.net/2199827728001/cN6vRtRQt_default/index.html?videoId=%s'

    def _real_extract(self, url):
        content_id = self._match_id(url)
        data = self._download_json(
            'https://10play.com.au/api/video/' + content_id, content_id)
        video = data.get('video') or {}
        metadata = data.get('metaData') or {}
        brightcove_id = video.get('videoId') or metadata['showContentVideoId']
        brightcove_url = smuggle_url(
            self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
            {'geo_countries': ['AU']})

        return {
            '_type': 'url_transparent',
            'url': brightcove_url,
            'id': content_id,
            'title': video.get('title') or metadata.get('pageContentName') or metadata.get('showContentName'),
            'description': video.get('description'),
            'age_limit': parse_age_limit(video.get('showRatingClassification') or metadata.get('showProgramClassification')),
            'series': metadata.get('showName'),
            'season': metadata.get('showContentSeason'),
            'timestamp': parse_iso8601(metadata.get('contentPublishDate') or metadata.get('pageContentPublishDate')),
            'ie_key': 'BrightcoveNew',
        }

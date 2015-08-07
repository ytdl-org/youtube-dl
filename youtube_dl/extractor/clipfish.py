from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    determine_ext,
)


class ClipfishIE(InfoExtractor):
    IE_NAME = 'clipfish'

    _VALID_URL = r'^https?://(?:www\.)?clipfish\.de/.*?/video/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.clipfish.de/special/game-trailer/video/3966754/fifa-14-e3-2013-trailer/',
        'md5': '79bc922f3e8a9097b3d68a93780fd475',
        'info_dict': {
            'id': '3966754',
            'ext': 'mp4',
            'title': 'FIFA 14 - E3 2013 Trailer',
            'duration': 82,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_info = self._parse_json(
            js_to_json(self._html_search_regex('var videoObject = ({[^}]+?})', webpage, 'videoObject')),
            video_id
        )
        info_url = self._parse_json(
            js_to_json(self._html_search_regex('var globalFlashvars = ({[^}]+?})', webpage, 'globalFlashvars')),
            video_id
        )['data']

        doc = self._download_xml(
            info_url, video_id, note='Downloading info page')
        title = doc.find('title').text
        video_url = doc.find('filename').text
        thumbnail = doc.find('imageurl').text
        duration = int_or_none(video_info['length'])
        formats = [{'url': video_info['videourl']},{'url': video_url}]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
        }

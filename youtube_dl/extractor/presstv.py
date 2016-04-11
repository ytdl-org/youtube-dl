# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import str_to_int


class PressTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?presstv\.ir/[^/]+/(?P<y>[0-9]+)/(?P<m>[0-9]+)/(?P<d>[0-9]+)/(?P<id>[0-9]+)/'

    _TEST = {
        'url': 'http://www.presstv.ir/Detail/2016/04/09/459911/Australian-sewerage-treatment-facility-/',
        'md5': '5d7e3195a447cb13e9267e931d8dd5a5',
        'info_dict': {
            'id': '459911',
            'ext': 'mp4',
            'title': 'Organic mattresses used to clean waste water',
            'upload_date': '20160409',
            'thumbnail': 're:^https?://.*\.jpg',
            'description': 'md5:20002e654bbafb6908395a5c0cfcd125'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # extract video URL from webpage
        video_url = self._html_search_regex(r'<input type="hidden" id="inpPlayback" value="([^"]+)" />', webpage,
                                            'Video URL')

        # build list of available formats
        # specified in http://www.presstv.ir/Scripts/playback.js
        base_url = 'http://192.99.219.222:82/presstv'
        _formats = [
            ("180p", "_low200.mp4"),
            ("360p", "_low400.mp4"),
            ("720p", "_low800.mp4"),
            ("1080p", ".mp4")
        ]

        formats = []
        for fmt in _formats:
            format_id, extension = fmt
            formats.append({
                'url': base_url + video_url[:-4] + extension,
                'format_id': format_id
            })

        # extract video metadata
        title = self._html_search_meta('title', webpage, 'Title', True)
        title = title.partition('-')[2].strip()

        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)

        match = re.match(PressTVIE._VALID_URL, url)
        upload_date = '%04d%02d%02d' % (
            str_to_int(match.group('y')),
            str_to_int(match.group('m')),
            str_to_int(match.group('d'))
        )

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'description': description
        }

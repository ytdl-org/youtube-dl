from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    sanitized_Request,
)

class PowerwatchIE(InfoExtractor):
    _VALID_URL = r'http://powerwatch\.pw/(?P<id>\w+)'

    _TEST = {
        'url': 'http://powerwatch.pw/duecjibvicbu',
        'md5': 'bf7965f70675be5e1a1749be3b8d20ba',
        'info_dict': {
            'id': 'duecjibvicbu',
            'ext': 'mp4',
            'title': 'Big Buck Bunny trailer',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        if '>File Not Found<' in webpage:
            raise ExtractorError('Video %s was not found' % video_id, expected=True)

        self._sleep(5, video_id)

        download_form = self._hidden_inputs(webpage)
        request = sanitized_Request(url, compat_urllib_parse.urlencode(download_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        video_page = self._download_webpage(request, video_id, 'Downloading video page')

        self.report_extraction(video_id)

        title = self._html_search_regex(
            r'h4-fine[^>]*>([^<]+)<', video_page, 'title')
        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', video_page, 'thumbnail URL', fatal=False)
        video_urls = list(re.findall(
            r'file:\s*"([^"]+)"', video_page))

        formats = []
        for video_url in video_urls:
            formats.append({
                'url': video_url,
                'ext': 'mp4',
            })

        self._sort_formats(formats)

        return {
            'formats': formats,
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
        }

from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    sanitized_Request,
)


class PrimeShareTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?primeshare\.tv/download/(?P<id>[\da-zA-Z]+)'

    _TEST = {
        'url': 'http://primeshare.tv/download/238790B611',
        'md5': 'b92d9bf5461137c36228009f31533fbc',
        'info_dict': {
            'id': '238790B611',
            'ext': 'mp4',
            'title': 'Public Domain - 1960s Commercial - Crest Toothpaste-YKsuFona',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if '>File not exist<' in webpage:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        fields = self._hidden_inputs(webpage)

        headers = {
            'Referer': url,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        wait_time = int(self._search_regex(
            r'var\s+cWaitTime\s*=\s*(\d+)',
            webpage, 'wait time', default=7)) + 1
        self._sleep(wait_time, video_id)

        req = sanitized_Request(
            url, compat_urllib_parse.urlencode(fields), headers)
        video_page = self._download_webpage(
            req, video_id, 'Downloading video page')

        video_url = self._search_regex(
            r"url\s*:\s*'([^']+\.primeshare\.tv(?::443)?/file/[^']+)'",
            video_page, 'video url')

        title = self._html_search_regex(
            r'<h1>Watch\s*(?:&nbsp;)?\s*\((.+?)(?:\s*\[\.\.\.\])?\)\s*(?:&nbsp;)?\s*<strong>',
            video_page, 'title')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'mp4',
        }

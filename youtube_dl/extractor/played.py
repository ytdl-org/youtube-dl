# coding: utf-8
from __future__ import unicode_literals

import re
import os.path

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    sanitized_Request,
)


class PlayedIE(InfoExtractor):
    IE_NAME = 'played.to'
    _VALID_URL = r'https?://(?:www\.)?played\.to/(?P<id>[a-zA-Z0-9_-]+)'

    _TEST = {
        'url': 'http://played.to/j2f2sfiiukgt',
        'md5': 'c2bd75a368e82980e7257bf500c00637',
        'info_dict': {
            'id': 'j2f2sfiiukgt',
            'ext': 'flv',
            'title': 'youtube-dl_test_video.mp4',
        },
        'skip': 'Removed for copyright infringement.',  # oh wow
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        orig_webpage = self._download_webpage(url, video_id)

        m_error = re.search(
            r'(?s)Reason for deletion:.*?<b class="err"[^>]*>(?P<msg>[^<]+)</b>', orig_webpage)
        if m_error:
            raise ExtractorError(m_error.group('msg'), expected=True)

        data = self._hidden_inputs(orig_webpage)

        self._sleep(2, video_id)

        post = compat_urllib_parse.urlencode(data)
        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        req = sanitized_Request(url, post, headers)
        webpage = self._download_webpage(
            req, video_id, note='Downloading video page ...')

        title = os.path.splitext(data['fname'])[0]

        video_url = self._search_regex(
            r'file: "?(.+?)",', webpage, 'video URL')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }

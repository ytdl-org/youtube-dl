# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import sanitized_Request


class VodlockerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vodlocker\.com/(?P<id>[0-9a-zA-Z]+)(?:\..*?)?'

    _TESTS = [{
        'url': 'http://vodlocker.com/e8wvyzz4sl42',
        'md5': 'ce0c2d18fa0735f1bd91b69b0e54aacf',
        'info_dict': {
            'id': 'e8wvyzz4sl42',
            'ext': 'mp4',
            'title': 'Germany vs Brazil',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        fields = self._hidden_inputs(webpage)

        if fields['op'] == 'download1':
            self._sleep(3, video_id)  # they do detect when requests happen too fast!
            post = compat_urllib_parse.urlencode(fields)
            req = sanitized_Request(url, post)
            req.add_header('Content-type', 'application/x-www-form-urlencoded')
            webpage = self._download_webpage(
                req, video_id, 'Downloading video page')

        title = self._search_regex(
            r'id="file_title".*?>\s*(.*?)\s*<(?:br|span)', webpage, 'title')
        thumbnail = self._search_regex(
            r'image:\s*"(http[^\"]+)",', webpage, 'thumbnail')
        url = self._search_regex(
            r'file:\s*"(http[^\"]+)",', webpage, 'file url')

        formats = [{
            'format_id': 'sd',
            'url': url,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

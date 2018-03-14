# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RequestForCommentsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?requestforcomments.de/(?:archives/|\?p=)(?P<id>[^\s]+)'
    _TESTS = [{
        'url': 'https://requestforcomments.de/archives/412',
        'info_dict': {
            'id': '412',
            'ext': 'ogg',
            'formats': 'mincount:4',
            'title': 'RFCE014: IPv6',
            'description': 'md5:e0924fc2a3536107c2055b3c36bef2e9',
            'site_name': 'Request for Comments',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://requestforcomments.de/?p=412',
        'info_dict': {
            'id': '412',
            'ext': 'ogg',
            'formats': 'mincount:4',
            'title': 'RFCE014: IPv6',
            'description': 'md5:e0924fc2a3536107c2055b3c36bef2e9',
            'site_name': 'Request for Comments',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):

        content_id = self._match_id(url).strip('/')
        webpage = self._download_webpage(url, content_id)

        audio_reg = self._og_regexes('audio')
        audio_type_reg = self._og_regexes('audio:type')

        formats = []
        for audio_url, audio_type in zip(
                re.findall(audio_reg[0], webpage),
                re.findall(audio_type_reg[0], webpage)):
            formats.append({
                'url': audio_url[0],
                'format_id': audio_type[0]})

        return {
            'id': content_id,
            'title': self._og_search_title(webpage),
            'site_name': self._og_search_property('site_name', webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }

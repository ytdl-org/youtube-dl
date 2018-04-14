# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class AcornTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?acorn\.tv/.*'

    _TEST = {
        'url': 'https://acorn.tv/darkages/thedarkagesanageoflight/the-clash-of-the-gods',
        'info_dict': {
            'id': 'ref:D7718E01',
            'ext': 'mp4',
            'title': 'The Dark Ages: An Age of Light, Episode 1: The Clash of the Gods',
            'description': 'DARKAGES_SR1_EP1',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 3575.2,
            'timestamp': 1435154967,
            'upload_date': '20150624',
            'uploader_id': '3047407010001',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['BrightcoveNew'],
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'video')

        video_id = re.findall(r'data-video-id=\"(.*)\"', webpage)[0]

        return self.url_result(
            'http://players.brightcove.net/3047407010001/default_default/index.html?videoId=%s'
            % video_id, 'BrightcoveNew')

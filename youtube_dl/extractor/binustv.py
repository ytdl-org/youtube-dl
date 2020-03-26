# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

# BINUS TV uses YouTube to host videos. However, it uses additional private APIs for other features (i.e. comments).
# This script only uses URLs from the BINUS TV Android app share API (https://binus.bedigital.co.id/app/share/video/).
# Videos from the main BINUS TV website (https://www.binus.tv/video/) can still be extracted using generic extractor.


class BinusTVAppIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?binus\.bedigital\.co\.id/app/share/video/[^\/]+/[^\/]+/(?P<id>[^/?\0]+)'
    _TEST = {
        'url': 'https://binus.bedigital.co.id/app/share/video/7/65156/headline-gerakan-stayforus-mulai-menggema-di-laman-media',
        'info_dict': {
            'id': 'mjH-3DDJLmU',
            'ext': 'mp4',
            'title': '[Headline] Gerakan #StayForUs Mulai Menggema di Laman Media',
            'upload_date': '20200323',
            'description': 'md5:a602c6fba2e474a0d5844489fe42f689',
            'uploader': 'BINUSTV Channel',
            'uploader_id': 'ChannelBINUSTV'
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        youtube_id = self._search_regex(r'https:\/\/i.ytimg.com\/vi\/([0-9A-Za-z-_]{11})\/default.jpg', webpage, 'youtube_id')

        # Returns the YouTube video
        return self.url_result(youtube_id, ie='Youtube')

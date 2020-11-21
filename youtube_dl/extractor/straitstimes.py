# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor


class StraitsTimesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?straitstimes\.com/(?:(?:-|\w|\d)+)/(?P<id>(?:-|\w|\d)+)'
    _TESTS = [
        {
            'url': 'https://www.straitstimes.com/singapore/making-money-and-still-doing-good',
            'md5': '727f9cd346abb921f04017a05a91490f',
            'info_dict': {
                'id': '6177936234001',
                'ext': 'mp4',
                'title': 'Turning Point: Reinventing the workspace with Grace Sai',
                'thumbnail': r're:^https?://.*\.jpg$',
                'description': 'md5:887bf288135b26c9f9ab63e31e30a83d',
                'timestamp': 1596892965,
                'uploader_id': '4800266888001',
                'upload_date': '20200808',
            },
        },
        {
            'url': 'https://www.straitstimes.com/singapore/community/generation-grit-deaf-but-not-defeated',
            'info_dict': {
                'id': '6198657822001',
                'ext': 'mp4',
                'title': 'Generation Grit: V. Yuogan',
                'thumbnail': r're:^https?://.*\.jpg$',
                'description': 'md5:e7558684e648146cb3f77b57c54bd62d',
                'timestamp': 1603204141,
                'uploader_id': '4800266888001',
                'upload_date': '20201020',
            }
        }
    ]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/4800266888001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        url_obj = (
            re.search(r'<iframe src="/embed/(?P<id>\d+)".*</iframe>', webpage)
            or re.search(r'<div.*resource="https://players.brightcove.net/4539381505001/default_default(?:/index.html)?\?videoId=(?P<id>\d+)">', webpage))

        brightcove_id = url_obj.group('id')
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id
        )

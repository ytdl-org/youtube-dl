# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor


class ChannelNewsAsiaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?channelnewsasia\.com/(?:(?:-|\w|\d)+)/(?:(?:-|\w|\d)+)/(?P<id>(?:-|\w|\d)+)'
    _TESTS = [
        {
            'url': 'https://www.channelnewsasia.com/news/video-on-demand/wizards-of-tech',
            'md5': 'ed9ed143052f0da3ee8a8fa59ba16870',
            'info_dict': {
                'id': 'w0ZWRzajE6qDPXDb7DSeaOCJ3bJ3GDqC',
                'ext': 'mp4',
                'title': 'Wizards Of Tech_2020_0_1_Body',
                'description': 'md5:b3882dd00e329e623a179465de9f5478',
            },
        },
        {
            'url': 'https://www.channelnewsasia.com/news/asia/removing-the-negative-influences-of-religion-in-tibet-video-13604084',
            'md5': 'ed846cfca037823fa6d3d0d7af8a4e8f',
            'info_dict': {
                'id': 'ljZjd0ajE6NNMhVJ3Gb-QfL1l0p-qW6-',
                'ext': 'mp4',
                'title': "Removing the 'negative influences of religion' in Tibet | Video",
                'description': 'md5:777989926133319de6f6501372175fbf',
            },
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        url_obj = (
            re.search(r'<div.*video-asset-id="(?P<id>(?:\d|\w|-)+)".*</div>', webpage, flags=re.DOTALL)
            or re.search(r'<div.*data-video-id="(?P<id>(?:\d|\w|-)+)".*</div>', webpage, flags=re.DOTALL))

        ooyala_id = url_obj.group('id')
        return self.url_result(
            'ooyala:' + ooyala_id, 'Ooyala', ooyala_id
        )

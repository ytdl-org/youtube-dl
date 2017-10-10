# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class SlidesLiveIE(InfoExtractor):
    _VALID_URL = r'https?://slideslive\.com/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://slideslive.com/38902413/gcc-ia16-backend',
        'md5': 'b29fcd6c6952d0c79c5079b0e7a07e6f',
        'info_dict': {
            'id': 'LMtgR8ba0b0',
            'ext': 'mp4',
            'title': '38902413: external video',
            'description': '3890241320170925-9-1yd6ech.mp4',
            'uploader': 'SlidesLive Administrator',
            'uploader_id': 'UC62SdArr41t_-_fX40QCLRw',
            'upload_date': '20170925',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            url, video_id, headers={'Accept': 'application/json'})
        service_name = video_data['video_service_name']
        if service_name == 'YOUTUBE':
            yt_video_id = video_data['video_service_id']
            return self.url_result(yt_video_id, 'Youtube', video_id=yt_video_id)
        else:
            raise ExtractorError(
                'Unsupported service name: {0}'.format(service_name), expected=True)

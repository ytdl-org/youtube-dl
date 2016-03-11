# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class DWIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dw\.com/(?:[^/]+/)+av-(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.dw.com/en/intelligent-light/av-19112290',
        'md5': '7372046e1815c5a534b43f3c3c36e6e9',
        'info_dict': {
            'id': '19112290',
            'ext': 'mp4',
            'title': 'Intelligent light',
            'description': 'md5:90e00d5881719f2a6a5827cb74985af1',
            'upload_date': '20160311',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = self._extract_smil_formats(
            'http://www.dw.com/smil/v-%s' % video_id, video_id,
            transform_source=lambda s: s.replace(
                'rtmp://tv-od.dw.de/flash/',
                'http://tv-download.dw.de/dwtv_video/flv/'))

        webpage = self._download_webpage(url, video_id)
        hidden_inputs = self._hidden_inputs(webpage)
        title = hidden_inputs['media_title']

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': hidden_inputs.get('preview_image'),
            'duration': int_or_none(hidden_inputs.get('file_duration')),
            'upload_date': hidden_inputs.get('display_date'),
            'formats': formats,
        }

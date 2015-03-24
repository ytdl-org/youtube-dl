from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class MporaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mpora\.(?:com|de)/videos/(?P<id>[^?#/]+)'
    IE_NAME = 'MPORA'

    _TEST = {
        'url': 'http://mpora.de/videos/AAdo8okx4wiz/embed?locale=de',
        'md5': 'a7a228473eedd3be741397cf452932eb',
        'info_dict': {
            'id': 'AAdo8okx4wiz',
            'ext': 'mp4',
            'title': 'Katy Curd -  Winter in the Forest',
            'duration': 416,
            'uploader': 'Peter Newman Media',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data_json = self._search_regex(
            [r"new FM\.Player\('[^']+',\s*(\{.*?)\).player;",
             r"new\s+FM\.Kaltura\.Player\('[^']+'\s*,\s*({.+?})\);"],
            webpage, 'json')
        data = self._parse_json(data_json, video_id)

        uploader = data['info_overlay'].get('username')
        duration = data['video']['duration'] // 1000
        thumbnail = data['video']['encodings']['sd']['poster']
        title = data['info_overlay']['title']

        formats = []
        for encoding_id, edata in data['video']['encodings'].items():
            for src in edata['sources']:
                width_str = self._search_regex(
                    r'_([0-9]+)\.[a-zA-Z0-9]+$', src['src'],
                    False, default=None)
                vcodec = src['type'].partition('/')[2]

                formats.append({
                    'format_id': encoding_id + '-' + vcodec,
                    'url': src['src'],
                    'vcodec': vcodec,
                    'width': int_or_none(width_str),
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'uploader': uploader,
            'duration': duration,
            'thumbnail': thumbnail,
        }

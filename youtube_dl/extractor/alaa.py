# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    int_or_none,
    url_or_none,
    parse_filesize,
    parse_duration,
)


class AlaaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?alaatv\.com/c/(?P<id>[0-9]+)'

    _TEST = {
        'url': 'https://alaatv.com/c/19680',
        'info_dict': {
            'id': '19680',
            'ext': 'mp4',
            'title': 'مجموعه، الگو و دنباله (قسمت ششم)، تست های 48 الی 55',
            'thumbnail': 'https://nodes.alaatv.com/media/thumbnails/582/582070sevt.jpg',
            'duration': 1800
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_details = self._download_json('https://alaatv.com/api/v2/c/{0}'.format(video_id), video_id)
        video_details = video_details['data']

        video_image = video_details.get('photo')

        def map_formats(v):
            return {
                "url": v.get("link"),
                "filesize": parse_filesize(v.get("size")),
                "format_id": v.get("res"),
                "ext": v.get("ext"),
            }

        formats = list(map(map_formats, video_details['file']['video']))

        return {
            'id': video_id,
            'title': video_details['title'],
            'formats': formats,
            'thumbnail': url_or_none(video_image),
            'duration': int_or_none(parse_duration(video_details.get('duration') + ":00"))
        }

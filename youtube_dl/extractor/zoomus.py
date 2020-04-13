# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    url_or_none,
    parse_filesize
)


class ZoomUSIE(InfoExtractor):
    IE_NAME = 'zoom.us'
    _VALID_URL = r'https://(?:.*).?zoom.us/rec(?:ording)?/play/(?P<id>[^?&=]{64})'

    _TEST = {
        'url': 'https://zoom.us/recording/play/SILVuCL4bFtRwWTtOCFQQxAsBQsJljFtm9e4Z_bvo-A8B-nzUSYZRNuPl3qW5IGK',
        'info_dict': {
            'md5': '031a5b379f1547a8b29c5c4c837dccf2',
            'title': "GAZ Transformational Tuesdays W/ Landon & Stapes",
            'id': "SILVuCL4bFtRwWTtOCFQQxAsBQsJljFtm9e4Z_bvo-A8B-nzUSYZRNuPl3qW5IGK",
            'ext': "mp4"
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_url = self._search_regex(r"viewMp4Url: \'(.*)\'", webpage, 'video url')
        title = self._html_search_regex([r"topic: \"(.*)\",", r"<title>(.*) - Zoom</title>"], webpage, 'title')
        viewResolvtionsWidth = self._search_regex(r"viewResolvtionsWidth: (\d*)", webpage, 'res width', fatal=False)
        viewResolvtionsHeight = self._search_regex(r"viewResolvtionsHeight: (\d*)", webpage, 'res height', fatal=False)
        fileSize = parse_filesize(self._search_regex(r"fileSize: \'(.+)\'", webpage, 'fileSize', fatal=False))

        formats = []
        formats.append({
            'url': url_or_none(video_url),
            'width': int_or_none(viewResolvtionsWidth),
            'height': int_or_none(viewResolvtionsHeight),
            'http_headers': {'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                             'Referer': 'https://zoom.us/'},
            'ext': "mp4",
            'filesize_approx': int_or_none(fileSize)
        })
        self._sort_formats(formats)

        return {
            'id': display_id,
            'title': title,
            'formats': formats
        }
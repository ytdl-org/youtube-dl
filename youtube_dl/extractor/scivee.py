from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class SciVeeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?scivee\.tv/node/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.scivee.tv/node/62352',
        'md5': 'b16699b74c9e6a120f6772a44960304f',
        'info_dict': {
            'id': '62352',
            'ext': 'mp4',
            'title': 'Adam Arkin at the 2014 DOE JGI Genomics of Energy & Environment Meeting',
            'description': 'md5:81f1710638e11a481358fab1b11059d7',
        },
        'skip': 'Not accessible from Travis CI server',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # annotations XML is malformed
        annotations = self._download_webpage(
            'http://www.scivee.tv/assets/annotations/%s' % video_id, video_id, 'Downloading annotations')

        title = self._html_search_regex(r'<title>([^<]+)</title>', annotations, 'title')
        description = self._html_search_regex(r'<abstract>([^<]+)</abstract>', annotations, 'abstract', fatal=False)
        filesize = int_or_none(self._html_search_regex(
            r'<filesize>([^<]+)</filesize>', annotations, 'filesize', fatal=False))

        formats = [
            {
                'url': 'http://www.scivee.tv/assets/audio/%s' % video_id,
                'ext': 'mp3',
                'format_id': 'audio',
            },
            {
                'url': 'http://www.scivee.tv/assets/video/%s' % video_id,
                'ext': 'mp4',
                'format_id': 'video',
                'filesize': filesize,
            },
        ]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': 'http://www.scivee.tv/assets/videothumb/%s' % video_id,
            'formats': formats,
        }

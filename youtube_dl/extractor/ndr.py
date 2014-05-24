# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    qualities,
)


class NDRIE(InfoExtractor):
    IE_NAME = 'ndr'
    IE_DESC = 'NDR.de - Mediathek'
    _VALID_URL = r'https?://www\.ndr\.de/.+?(?P<id>\d+)\.html'

    _TESTS = [
        {
            'url': 'http://www.ndr.de/fernsehen/sendungen/markt/markt7959.html',
            'md5': 'e7a6079ca39d3568f4996cb858dd6708',
            'note': 'Video file',
            'info_dict': {
                'id': '7959',
                'ext': 'mp4',
                'title': 'Markt - die ganze Sendung',
                'description': 'md5:af9179cf07f67c5c12dc6d9997e05725',
                'duration': 2655,
            },
        },
        {
            'url': 'http://www.ndr.de/info/audio51535.html',
            'md5': 'bb3cd38e24fbcc866d13b50ca59307b8',
            'note': 'Audio file',
            'info_dict': {
                'id': '51535',
                'ext': 'mp3',
                'title': 'La Valette entgeht der Hinrichtung',
                'description': 'md5:22f9541913a40fe50091d5cdd7c9f536',
                'duration': 884,
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        title = self._og_search_title(page).strip()
        description = self._og_search_description(page)
        if description:
            description = description.strip()

        duration = int_or_none(self._html_search_regex(r'duration: (\d+),\n', page, 'duration', fatal=False))

        formats = []

        mp3_url = re.search(r'''\{src:'(?P<audio>[^']+)', type:"audio/mp3"},''', page)
        if mp3_url:
            formats.append({
                'url': mp3_url.group('audio'),
                'format_id': 'mp3',
            })

        thumbnail = None

        video_url = re.search(r'''3: \{src:'(?P<video>.+?)\.hi\.mp4', type:"video/mp4"},''', page)
        if video_url:
            thumbnails = re.findall(r'''\d+: \{src: "([^"]+)"(?: \|\| '[^']+')?, quality: '([^']+)'}''', page)
            if thumbnails:
                quality_key = qualities(['xs', 's', 'm', 'l', 'xl'])
                largest = max(thumbnails, key=lambda thumb: quality_key(thumb[1]))
                thumbnail = 'http://www.ndr.de' + largest[0]

            for format_id in 'lo', 'hi', 'hq':
                formats.append({
                    'url': '%s.%s.mp4' % (video_url.group('video'), format_id),
                    'format_id': format_id,
                })

        if not formats:
            raise ExtractorError('No media links available for %s' % video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
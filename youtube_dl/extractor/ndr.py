# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    qualities,
    parse_duration,
)


class NDRBaseIE(InfoExtractor):
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        title = self._og_search_title(page).strip()
        description = self._og_search_description(page)
        if description:
            description = description.strip()

        duration = int_or_none(self._html_search_regex(r'duration: (\d+),\n', page, 'duration', default=None))
        if not duration:
            duration = parse_duration(self._html_search_regex(
                r'(<span class="min">\d+</span>:<span class="sec">\d+</span>)',
                page, 'duration', default=None))

        formats = []

        mp3_url = re.search(r'''\{src:'(?P<audio>[^']+)', type:"audio/mp3"},''', page)
        if mp3_url:
            formats.append({
                'url': mp3_url.group('audio'),
                'format_id': 'mp3',
            })

        thumbnail = None

        video_url = re.search(r'''3: \{src:'(?P<video>.+?)\.(lo|hi|hq)\.mp4', type:"video/mp4"},''', page)
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


class NDRIE(NDRBaseIE):
    IE_NAME = 'ndr'
    IE_DESC = 'NDR.de - Mediathek'
    _VALID_URL = r'https?://www\.ndr\.de/.+?(?P<id>\d+)\.html'

    _TESTS = [
        {
            'url': 'http://www.ndr.de/fernsehen/sendungen/nordmagazin/Kartoffeltage-in-der-Lewitz,nordmagazin25866.html',
            'md5': '5bc5f5b92c82c0f8b26cddca34f8bb2c',
            'note': 'Video file',
            'info_dict': {
                'id': '25866',
                'ext': 'mp4',
                'title': 'Kartoffeltage in der Lewitz',
                'description': 'md5:48c4c04dde604c8a9971b3d4e3b9eaa8',
                'duration': 166,
            },
            'skip': '404 Not found',
        },
        {
            'url': 'http://www.ndr.de/fernsehen/Party-Poette-und-Parade,hafengeburtstag988.html',
            'md5': 'dadc003c55ae12a5d2f6bd436cd73f59',
            'info_dict': {
                'id': '988',
                'ext': 'mp4',
                'title': 'Party, Pötte und Parade',
                'description': 'Hunderttausende feiern zwischen Speicherstadt und St. Pauli den 826. Hafengeburtstag. Die NDR Sondersendung zeigt die schönsten und spektakulärsten Bilder vom Auftakt.',
                'duration': 3498,
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


class NJoyIE(NDRBaseIE):
    IE_NAME = 'N-JOY'
    _VALID_URL = r'https?://www\.n-joy\.de/.+?(?P<id>\d+)\.html'

    _TEST = {
        'url': 'http://www.n-joy.de/entertainment/comedy/comedy_contest/Benaissa-beim-NDR-Comedy-Contest,comedycontest2480.html',
        'md5': 'cb63be60cd6f9dd75218803146d8dc67',
        'info_dict': {
            'id': '2480',
            'ext': 'mp4',
            'title': 'Benaissa beim NDR Comedy Contest',
            'description': 'Von seinem sehr "behaarten" Leben lässt sich Benaissa trotz aller Schwierigkeiten nicht unterkriegen.',
            'duration': 654,
        }
    }

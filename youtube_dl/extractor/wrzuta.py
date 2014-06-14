# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    qualities,
)


class WrzutaIE(InfoExtractor):
    IE_NAME = 'wrzuta.pl'

    _VALID_URL = r'https?://(?P<uploader>[0-9a-zA-Z]+)\.wrzuta\.pl/(?P<typ>film|audio)/(?P<id>[0-9a-zA-Z]+)'

    _TESTS = [{
        'url': 'http://laboratoriumdextera.wrzuta.pl/film/aq4hIZWrkBu/nike_football_the_last_game',
        'md5': '9e67e05bed7c03b82488d87233a9efe7',
        'info_dict': {
            'id': 'aq4hIZWrkBu',
            'ext': 'mp4',
            'title': 'Nike Football: The Last Game',
            'duration': 307,
            'uploader_id': 'laboratoriumdextera',
            'description': 'md5:7fb5ef3c21c5893375fda51d9b15d9cd',
        },
    }, {
        'url': 'http://w729.wrzuta.pl/audio/9oXJqdcndqv/david_guetta_amp_showtek_ft._vassy_-_bad',
        'md5': '1e546a18e1c22ac6e9adce17b8961ff5',
        'info_dict': {
            'id': '9oXJqdcndqv',
            'ext': 'ogg',
            'title': 'David Guetta & Showtek ft. Vassy - Bad',
            'duration': 270,
            'uploader_id': 'w729',
            'description': 'md5:4628f01c666bbaaecefa83476cfa794a',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        typ = mobj.group('typ')
        uploader = mobj.group('uploader')

        webpage = self._download_webpage(url, video_id)

        quality = qualities(['SD', 'MQ', 'HQ', 'HD'])

        audio_table = {'flv': 'mp3', 'webm': 'ogg'}

        embedpage = self._download_json('http://www.wrzuta.pl/npp/embed/%s/%s' % (uploader, video_id), video_id)

        formats = []
        for media in embedpage['url']:
            if typ == 'audio':
                ext = audio_table[media['type'].split('@')[0]]
            else:
                ext = media['type'].split('@')[0]

            formats.append({
                'format_id': '%s_%s' % (ext, media['quality'].lower()),
                'url': media['url'],
                'ext': ext,
                'quality': quality(media['quality']),
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'duration': int_or_none(embedpage['duration']),
            'uploader_id': uploader,
            'description': self._og_search_description(webpage),
            'age_limit': embedpage.get('minimalAge', 0),
        }

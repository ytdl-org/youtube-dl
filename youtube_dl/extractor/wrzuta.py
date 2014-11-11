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
        'url': 'http://jolka85.wrzuta.pl/audio/063jOPX5ue2/liber_natalia_szroeder_-_teraz_ty',
        'md5': 'bc78077859bea7bcfe4295d7d7fc9025',
        'info_dict': {
            'id': '063jOPX5ue2',
            'ext': 'ogg',
            'title': 'Liber & Natalia Szroeder - Teraz Ty',
            'duration': 203,
            'uploader_id': 'jolka85',
            'description': 'md5:2d2b6340f9188c8c4cd891580e481096',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        typ = mobj.group('typ')
        uploader = mobj.group('uploader')

        webpage = self._download_webpage(url, video_id)

        quality = qualities(['SD', 'MQ', 'HQ', 'HD'])

        audio_table = {'flv': 'mp3', 'webm': 'ogg', '???': 'mp3'}

        embedpage = self._download_json('http://www.wrzuta.pl/npp/embed/%s/%s' % (uploader, video_id), video_id)

        formats = []
        for media in embedpage['url']:
            fmt = media['type'].split('@')[0]
            if typ == 'audio':
                ext = audio_table.get(fmt, fmt)
            else:
                ext = fmt

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

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


_ENTRY_PATTERN = r'<a href="(?P<playlist_entry_url>[^"]+)" target="_blank" class="playlist\-file\-page">'
_PLAYLIST_SIZE_PATTERN = r'<div class="playlist-counter">[0-9]+/([0-9]+)</div>'


class WrzutaPlaylistIE(InfoExtractor):
    """
        this class covers extraction of wrzuta playlist entries
        the extraction process bases on following steps:
        * collect information of playlist size
        * download all entries provided on
          the playlist webpage (the playlist is split
          on two pages: first directly reached from webpage
          second: downloaded on demand by ajax call and rendered
          using the ajax call response)
        * in case size of extracted entries not reached total number of entries
          use the ajax call to collect the remaining entries
    """

    IE_NAME = 'wrzuta.pl:playlist'

    _VALID_URL = r'https?://(?P<uploader>[0-9a-zA-Z]+)\.wrzuta\.pl/playlista/' \
                 '(?P<id>[0-9a-zA-Z]+)/.*'

    _TESTS = [{
        'url': 'http://miromak71.wrzuta.pl/playlista/7XfO4vE84iR/moja_muza',
        'playlist_mincount': 14,
        'info_dict': {
            'id': '7XfO4vE84iR',
            'title': 'Moja muza',
        },
    }, {
        'url': 'http://heroesf70.wrzuta.pl/playlista/6Nj3wQHx756/lipiec_-_lato_2015_muzyka_swiata',
        'playlist_mincount': 144,
        'info_dict': {
            'id': '6Nj3wQHx756',
            'title': 'Lipiec - Lato 2015 Muzyka Świata',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        uploader = mobj.group('uploader')

        entries = []

        webpage = self._download_webpage(url, playlist_id)

        playlist_size = self._html_search_regex(_PLAYLIST_SIZE_PATTERN, webpage, 'Size of the playlist')
        playlist_size = int(playlist_size) if playlist_size else 0

        playlist_title = self._og_search_title(webpage).replace('Playlista: ', '', 1)

        if playlist_size:
            entries = list(map(
                lambda entry_url: self.url_result(entry_url),
                re.findall(_ENTRY_PATTERN, webpage)
            ))

            if playlist_size > len(entries):
                playlist_content = self._download_json(
                    'http://{uploader_id}.wrzuta.pl/xhr/get_playlist_offset/{playlist_id}'.format(
                        uploader_id=uploader,
                        playlist_id=playlist_id,
                    ),
                    playlist_id,
                    'Downloading playlist content as JSON metadata',
                    'Unable to download playlist content as JSON metadata',
                )
                entries += [self.url_result(entry['filelink']) for entry in playlist_content['files']]

        return self.playlist_result(entries, playlist_id, playlist_title)

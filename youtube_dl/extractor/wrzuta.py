# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    qualities,
    remove_start,
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
        'skip': 'Redirected to wrzuta.pl',
    }, {
        'url': 'http://vexling.wrzuta.pl/audio/01xBFabGXu6/james_horner_-_into_the_na_39_vi_world_bonus',
        'md5': 'f80564fb5a2ec6ec59705ae2bf2ba56d',
        'info_dict': {
            'id': '01xBFabGXu6',
            'ext': 'mp3',
            'title': 'James Horner - Into The Na\'vi World [Bonus]',
            'description': 'md5:30a70718b2cd9df3120fce4445b0263b',
            'duration': 95,
            'uploader_id': 'vexling',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        typ = mobj.group('typ')
        uploader = mobj.group('uploader')

        webpage, urlh = self._download_webpage_handle(url, video_id)

        if urlh.geturl() == 'http://www.wrzuta.pl/':
            raise ExtractorError('Video removed', expected=True)

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
    _VALID_URL = r'https?://(?P<uploader>[0-9a-zA-Z]+)\.wrzuta\.pl/playlista/(?P<id>[0-9a-zA-Z]+)'
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
    }, {
        'url': 'http://miromak71.wrzuta.pl/playlista/7XfO4vE84iR',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        uploader = mobj.group('uploader')

        webpage = self._download_webpage(url, playlist_id)

        playlist_size = int_or_none(self._html_search_regex(
            (r'<div[^>]+class=["\']playlist-counter["\'][^>]*>\d+/(\d+)',
             r'<div[^>]+class=["\']all-counter["\'][^>]*>(.+?)</div>'),
            webpage, 'playlist size', default=None))

        playlist_title = remove_start(
            self._og_search_title(webpage), 'Playlista: ')

        entries = []
        if playlist_size:
            entries = [
                self.url_result(entry_url)
                for _, entry_url in re.findall(
                    r'<a[^>]+href=(["\'])(http.+?)\1[^>]+class=["\']playlist-file-page',
                    webpage)]
            if playlist_size > len(entries):
                playlist_content = self._download_json(
                    'http://%s.wrzuta.pl/xhr/get_playlist_offset/%s' % (uploader, playlist_id),
                    playlist_id,
                    'Downloading playlist JSON',
                    'Unable to download playlist JSON')
                entries.extend([
                    self.url_result(entry['filelink'])
                    for entry in playlist_content.get('files', []) if entry.get('filelink')])

        return self.playlist_result(entries, playlist_id, playlist_title)

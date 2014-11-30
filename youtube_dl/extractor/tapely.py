# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    compat_urllib_request,
    float_or_none,
    parse_iso8601,
)


class TapelyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tape\.ly/(?P<id>[A-Za-z0-9\-_]+)(?:/(?P<songnr>\d+))?'
    _API_URL = 'http://tape.ly/showtape?id={0:}'
    _S3_SONG_URL = 'http://mytape.s3.amazonaws.com/{0:}'
    _SOUNDCLOUD_SONG_URL = 'http://api.soundcloud.com{0:}'
    _TESTS = [
        {
            'url': 'http://tape.ly/my-grief-as-told-by-water',
            'info_dict': {
                'id': 23952,
                'title': 'my grief as told by water',
                'thumbnail': 're:^https?://.*\.png$',
                'uploader_id': 16484,
                'timestamp': 1411848286,
                'description': 'For Robin and Ponkers, whom the tides of life have taken out to sea.',
            },
            'playlist_count': 13,
        },
        {
            'url': 'http://tape.ly/my-grief-as-told-by-water/1',
            'md5': '79031f459fdec6530663b854cbc5715c',
            'info_dict': {
                'id': 258464,
                'title': 'Dreaming Awake  (My Brightest Diamond)',
                'ext': 'm4a',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        playlist_url = self._API_URL.format(display_id)
        request = compat_urllib_request.Request(playlist_url)
        request.add_header('X-Requested-With', 'XMLHttpRequest')
        request.add_header('Accept', 'application/json')
        request.add_header('Referer', url)

        playlist = self._download_json(request, display_id)

        tape = playlist['tape']

        entries = []
        for s in tape['songs']:
            song = s['song']
            entry = {
                'id': song['id'],
                'duration': float_or_none(song.get('songduration'), 1000),
                'title': song['title'],
            }
            if song['source'] == 'S3':
                entry.update({
                    'url': self._S3_SONG_URL.format(song['filename']),
                })
                entries.append(entry)
            elif song['source'] == 'YT':
                self.to_screen('YouTube video detected')
                yt_id = song['filename'].replace('/youtube/', '')
                entry.update(self.url_result(yt_id, 'Youtube', video_id=yt_id))
                entries.append(entry)
            elif song['source'] == 'SC':
                self.to_screen('SoundCloud song detected')
                sc_url = self._SOUNDCLOUD_SONG_URL.format(song['filename'])
                entry.update(self.url_result(sc_url, 'Soundcloud'))
                entries.append(entry)
            else:
                self.report_warning('Unknown song source: %s' % song['source'])

        if mobj.group('songnr'):
            songnr = int(mobj.group('songnr')) - 1
            try:
                return entries[songnr]
            except IndexError:
                raise ExtractorError(
                    'No song with index: %s' % mobj.group('songnr'),
                    expected=True)

        return {
            '_type': 'playlist',
            'id': tape['id'],
            'display_id': display_id,
            'title': tape['name'],
            'entries': entries,
            'thumbnail': tape.get('image_url'),
            'description': clean_html(tape.get('subtext')),
            'like_count': tape.get('likescount'),
            'uploader_id': tape.get('user_id'),
            'timestamp': parse_iso8601(tape.get('published_at')),
        }

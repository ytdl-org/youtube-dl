# coding: utf-8
from __future__ import unicode_literals

import random
import re
import string
import time

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    urlencode_postdata,
)


class JioSaavnBaseInfoExtractor(InfoExtractor):
    def extract_initial_data_as_json(self, url, id):
        webpage = self._download_webpage(url, id)
        init_data_re = r'window.__INITIAL_DATA__\s*=\s*(?P<json>.+?);*\s*\</script>'

        def sanitize_init_data(init_data):
            new_date_call_re = r'new Date\(.+?\)'
            return re.sub(new_date_call_re, '"%s"' % time.ctime(), unescapeHTML(init_data))

        init_data = self._parse_json(self._search_regex(init_data_re, webpage,
                                                        'init-json'),
                                     id, transform_source=sanitize_init_data)
        return init_data


class JioSaavnSongIE(JioSaavnBaseInfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:www\.)?
                        (?:
                            jiosaavn\.com/song/[^/]+/|
                            saavn.com/s/song/(?:[^/]+/){3}
                        )
                        (?P<id>[\w\d]+)
                   '''
    _TESTS = [{
        'url': 'https://www.jiosaavn.com/song/leja-re/OQsEfQFVUXk',
        'md5': '7b1f70de088ede3a152ea34aece4df42',
        'info_dict': {
            'id': 'OQsEfQFVUXk',
            'ext': 'mp3',
            'title': 'Leja Re',
            'album': 'Leja Re',
        },
    }, {
        'url': 'https://www.saavn.com/s/song/hindi/Saathiya/O-Humdum-Suniyo-Re/KAMiazoCblU',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        fp = ''.join([random.choice(string.hexdigits) for _ in range(32)])

        # This is required, else server won't return the media_url (extracted below)
        self._download_webpage('https://www.jiosaavn.com/stats.php', audio_id,
                               query={
                                   'ev': 'site:browser:fp',
                                   'fp': fp,
                                   '_t': int(time.time()),
                                   'ct': '00000000',
                               })

        song_data = self.extract_initial_data_as_json(url, audio_id)['song']['song']

        data = urlencode_postdata({'__call': 'song.generateAuthToken',
                                   '_format': 'json',
                                   'bitrate': '128',
                                   'url': song_data['encrypted_media_url'],
                                   })

        def clean_api_json(resp):
            return self._search_regex(r'(?P<json>\{.+?})', resp, 'api-json')

        media_url = self._download_json('https://www.jiosaavn.com/api.php',
                                        audio_id, data=data,
                                        transform_source=clean_api_json,
                                        )['auth_url']

        return {
            'id': audio_id,
            'title': song_data['title']['text'],
            'formats': [{
                'url': media_url,
                'ext': 'mp3',
                'format_note': 'MPEG audio',
                'format_id': '128',
                'vcodec': 'none',
            }],
            'album': song_data.get('album', {}).get('text'),
            'thumbnail': song_data.get('image', [None])[0],
        }


class JioSaavnAlbumIE(JioSaavnBaseInfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:www\.)?
                        (?:(?:jio)?saavn\.com/album/[^/]+/)
                        (?P<id>[\w\d]+)
                   '''
    _TESTS = [{
        'url': 'https://www.jiosaavn.com/album/96/buIOjYZDrNA_',
        'info_dict': {
            'id': 'buIOjYZDrNA_',
            'title': '96',
        },
        'playlist_count': 10,
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)
        album_data = self.extract_initial_data_as_json(url, album_id)['albumView']['album']
        songs = [self.url_result(song['perma_url']) for song in album_data['songs']]

        return self.playlist_result(songs, album_id, album_data.get('title', {}).get('text'))

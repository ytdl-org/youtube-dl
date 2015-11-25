from __future__ import unicode_literals

import re
import json
import itertools

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    ExtractorError,
    HEADRequest,
    str_to_int,
)


class MixcloudIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([^/]+)/([^/]+)'
    IE_NAME = 'mixcloud'

    _TESTS = [{
        'url': 'http://www.mixcloud.com/dholbach/cryptkeeper/',
        'info_dict': {
            'id': 'dholbach-cryptkeeper',
            'ext': 'mp3',
            'title': 'Cryptkeeper',
            'description': 'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            'uploader': 'Daniel Holbach',
            'uploader_id': 'dholbach',
            'thumbnail': 're:https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
        },
    }, {
        'url': 'http://www.mixcloud.com/gillespeterson/caribou-7-inch-vinyl-mix-chat/',
        'info_dict': {
            'id': 'gillespeterson-caribou-7-inch-vinyl-mix-chat',
            'ext': 'mp3',
            'title': 'Caribou 7 inch Vinyl Mix & Chat',
            'description': 'md5:2b8aec6adce69f9d41724647c65875e8',
            'uploader': 'Gilles Peterson Worldwide',
            'uploader_id': 'gillespeterson',
            'thumbnail': 're:https?://.*/images/',
            'view_count': int,
            'like_count': int,
        },
    }, {
        'url': 'https://www.mixcloud.com/freshlifechurch/moment-maker/',
        'md5': 'b8cbf9ec43e1ae5c9a1757087692d384',
        'info_dict': {
            'id': 'freshlifechurch-moment-maker',
            'ext': 'mp3',
            'title': 'Moment Maker',
            'description': 'md5:ed6ac0493c017b5200a88bb4716663b6',
            'uploader': 'fresh life church',
            'uploader_id': 'freshlifechurch',
            'thumbnail': 're:https?://.*/images/',
        },
    }]

    def _check_url(self, url, track_id, ext):
        try:
            # We only want to know if the request succeed
            # don't download the whole file
            self._request_webpage(
                HEADRequest(url), track_id,
                'Trying %s URL' % ext)
            return True
        except ExtractorError:
            return False

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = compat_urllib_parse_unquote('-'.join((uploader, cloudcast_name)))

        webpage = self._download_webpage(url, track_id)

        preview_url = self._search_regex(
            r'\s(?:data-preview-url|m-preview)="([^"]+)"', webpage, 'preview url', default=None)
        if preview_url is not None:
            song_url = preview_url.replace('/previews/', '/c/originals/')
            if not self._check_url(song_url, track_id, 'mp3'):
                song_url = song_url.replace('.mp3', '.m4a').replace('originals/', 'm4a/64/')
                if not self._check_url(song_url, track_id, 'm4a'):
                    raise ExtractorError('Unable to extract track url')
        else:
            play_info_encoded = self._search_regex(
                r'\sm-play-info="([^"]+)"', webpage, 'preview url').decode('base64')
            secret = 'cGxlYXNlZG9udGRvd25sb2Fkb3VybXVzaWN0aGVhcnRpc3Rzd29udGdldHBhaWQ='.decode('base64')
            play_info_json = ''.join(chr(ord(a) ^ ord(b)) for a, b in itertools.izip(play_info_encoded, itertools.cycle(secret)))
            play_info = json.loads(play_info_json)
            song_url = play_info.get('stream_url')

        PREFIX = (
            r'm-play-on-spacebar[^>]+'
            r'(?:\s+[a-zA-Z0-9-]+(?:="[^"]+")?)*?\s+')
        title = self._html_search_regex(
            PREFIX + r'm-title="([^"]+)"', webpage, 'title')
        thumbnail = self._proto_relative_url(self._html_search_regex(
            PREFIX + r'm-thumbnail-url="([^"]+)"', webpage, 'thumbnail',
            fatal=False))
        uploader = self._html_search_regex(
            PREFIX + r'm-owner-name="([^"]+)"',
            webpage, 'uploader', fatal=False)
        uploader_id = self._search_regex(
            r'\s+"profile": "([^"]+)",', webpage, 'uploader id', fatal=False)
        description = self._og_search_description(webpage)
        like_count = str_to_int(self._search_regex(
            r'\bbutton-favorite\b[^>]+m-ajax-toggle-count="([^"]+)"',
            webpage, 'like count', default=None))
        view_count = str_to_int(self._search_regex(
            [r'<meta itemprop="interactionCount" content="UserPlays:([0-9]+)"',
             r'/listeners/?">([0-9,.]+)</a>'],
            webpage, 'play count', default=None))

        return {
            'id': track_id,
            'title': title,
            'url': song_url,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'like_count': like_count,
        }

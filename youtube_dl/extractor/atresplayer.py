from __future__ import unicode_literals

import json
from urllib.error import HTTPError

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError




class AtresPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?atresplayer\.com/[^/]+/[^/]+/[^/]+/[^/]+/[^/_]+_(?P<id>[A-z0-9]+)/?'
    _NETRC_MACHINE = 'atresplayer'
    _TESTS = [
        {
            'url': 'https://www.atresplayer.com/lasexta/series/navy-investigacion-criminal/temporada-12/capitulo-10-captulo_5ad6869b986b2866f89ebca0/',
            'md5': '3afa3d3cc155264374916f2a23d1d00c',
            'info_dict': {
                'id': '5ad6869b986b2866f89ebca0',
                'ext': 'm3u8',
                'title': u'Capítulo 10: Reglas de casa',
                'description': 'md5:3ec43e9b7da2cd1280fa80adccdd09b0',
                'duration': 2500.0,
                'thumbnail': r're:^https://imagenes.atresplayer.com/.+$'
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.atresplayer.com/television/series/el-secreto-de-puente-viejo/el-chico-de-los-tres-lunares/capitulo-977-29-12-14_2014122400174.html',
            'only_matching': True,
        },
    ]

    _USER_AGENT = 'Dalvik/1.6.0 (Linux; U; Android 4.3; GT-I9300 Build/JSS15J'

    _PLAYER_URL_TEMPLATE = 'https://api.atresplayer.com/client/v1/page/episode/%s'

    _LOGIN_URL = 'https://api.atresplayer.com/login?redirect=https%3A%2F%2Fwww.atresplayer.com'
    _LOGIN_ACCOUNT_URL = 'https://account.atresmedia.com/api/login'


    def _real_initialize(self):
        self._login()

    def _login(self):

        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'username': username,
            'password': password,
        }

        self._download_webpage(self._LOGIN_URL, None, 'get login page')
        request = sanitized_Request(
            self._LOGIN_ACCOUNT_URL,
            urlencode_postdata(login_form),
            login_form,
            method='post')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        # request.add_header('Content-Type', 'multipart/form-data')
        try:
            response = self._download_json(
                request, None, 'post to login form')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError):
                self._atres_player_error(e.cause.file.read(), e)
            else:
                raise
        else:
            self._download_webpage(response['targetUrl'], None, 'Set login session')

    def _atres_player_error(self, body_response, original_exception):
        try:
            data = json.loads(body_response)
        except JSONDecodeError:
            raise original_exception
        if isinstance(data, dict) and 'error' in data:
            raise ExtractorError('{} returned error: {} ({})'.format(
                self.IE_NAME, data['error'], data.get('error_description', 'There is no description')
            ), expected=True)
        else:
            raise original_exception

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = sanitized_Request(
            self._PLAYER_URL_TEMPLATE % video_id,
            headers={'User-Agent': self._USER_AGENT})
        player = self._download_json(request, video_id, 'Downloading player JSON')

        formats = []
        video_url = player.get('urlVideo')

        request = sanitized_Request(
            video_url,
            headers={'User-Agent': self._USER_AGENT})
        try:
            video_data = self._download_json(request, video_id, 'Downloading video JSON', fatal=True)
        except ExtractorError as e:
            if len(e.exc_info) <= 1 or e.exc_info[1].code != 403:
                raise
            self._atres_player_error(e.exc_info[1].file.read(), e)

        for source in video_data['sources']:
            if source['type'] == "application/dash+xml":
                formats.extend(self._extract_mpd_formats(
                    source['src'], video_id, mpd_id='dash',
                    fatal=False))
            elif source['type'] == "application/vnd.apple.mpegurl":
                formats.extend(self._extract_m3u8_formats(
                    source['src'], video_id,
                    fatal=False))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['titulo'],
            'description': video_data['descripcion'],
            'thumbnail': video_data['imgPoster'],
            'duration': video_data['duration'],
            'formats': formats,
        }

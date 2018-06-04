from __future__ import unicode_literals

import time
import hmac
import hashlib
import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    sanitized_Request,
    urlencode_postdata,
    xpath_text,
)


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

    _LOGIN_URL = 'https://servicios.atresplayer.com/j_spring_security_check'

    _ERRORS = {
        'UNPUBLISHED': 'We\'re sorry, but this video is not yet available.',
        'DELETED': 'This video has expired and is no longer available for online streaming.',
        'GEOUNPUBLISHED': 'We\'re sorry, but this video is not available in your region due to right restrictions.',
        # 'PREMIUM': 'PREMIUM',
    }

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'j_username': username,
            'j_password': password,
        }

        request = sanitized_Request(
            self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        response = self._download_webpage(
            request, None, 'Logging in')

        error = self._html_search_regex(
            r'(?s)<ul[^>]+class="[^"]*\blist_error\b[^"]*">(.+?)</ul>',
            response, 'error', default=None)
        if error:
            raise ExtractorError(
                'Unable to login: %s' % error, expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = sanitized_Request(
            self._PLAYER_URL_TEMPLATE % video_id,
            headers={'User-Agent': self._USER_AGENT})
        player = self._download_json(request, video_id, 'Downloading player JSON')

        episode_type = player.get('typeOfEpisode')
        error_message = self._ERRORS.get(episode_type)
        if error_message:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_message), expected=True)

        formats = []
        video_url = player.get('urlVideo')

        request = sanitized_Request(
            video_url,
            headers={'User-Agent': self._USER_AGENT})
        video_data = self._download_json(request, video_id, 'Downloading video JSON')

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

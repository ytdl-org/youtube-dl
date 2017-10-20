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
    _VALID_URL = r'https?://(?:www\.)?atresplayer\.com/television/[^/]+/[^/]+/[^/]+/(?P<id>.+?)_\d+\.html'
    _NETRC_MACHINE = 'atresplayer'
    _TESTS = [
        {
            'url': 'http://www.atresplayer.com/television/programas/el-club-de-la-comedia/temporada-4/capitulo-10-especial-solidario-nochebuena_2014122100174.html',
            'md5': 'efd56753cda1bb64df52a3074f62e38a',
            'info_dict': {
                'id': 'capitulo-10-especial-solidario-nochebuena',
                'ext': 'mp4',
                'title': 'Especial Solidario de Nochebuena',
                'description': 'md5:e2d52ff12214fa937107d21064075bf1',
                'duration': 5527.6,
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'skip': 'This video is only available for registered users'
        },
        {
            'url': 'http://www.atresplayer.com/television/especial/videoencuentros/temporada-1/capitulo-112-david-bustamante_2014121600375.html',
            'md5': '6e52cbb513c405e403dbacb7aacf8747',
            'info_dict': {
                'id': 'capitulo-112-david-bustamante',
                'ext': 'flv',
                'title': 'David Bustamante',
                'description': 'md5:f33f1c0a05be57f6708d4dd83a3b81c6',
                'duration': 1439.0,
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://www.atresplayer.com/television/series/el-secreto-de-puente-viejo/el-chico-de-los-tres-lunares/capitulo-977-29-12-14_2014122400174.html',
            'only_matching': True,
        },
    ]

    _USER_AGENT = 'Dalvik/1.6.0 (Linux; U; Android 4.3; GT-I9300 Build/JSS15J'
    _MAGIC = 'QWtMLXs414Yo+c#_+Q#K@NN)'
    _TIMESTAMP_SHIFT = 30000

    _TIME_API_URL = 'http://servicios.atresplayer.com/api/admin/time.json'
    _URL_VIDEO_TEMPLATE = 'https://servicios.atresplayer.com/api/urlVideo/{1}/{0}/{1}|{2}|{3}.json'
    _PLAYER_URL_TEMPLATE = 'https://servicios.atresplayer.com/episode/getplayer.json?episodePk=%s'
    _EPISODE_URL_TEMPLATE = 'http://www.atresplayer.com/episodexml/%s'

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
            request, None, 'Logging in as %s' % username)

        error = self._html_search_regex(
            r'(?s)<ul[^>]+class="[^"]*\blist_error\b[^"]*">(.+?)</ul>',
            response, 'error', default=None)
        if error:
            raise ExtractorError(
                'Unable to login: %s' % error, expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        episode_id = self._search_regex(
            r'episode="([^"]+)"', webpage, 'episode id')

        request = sanitized_Request(
            self._PLAYER_URL_TEMPLATE % episode_id,
            headers={'User-Agent': self._USER_AGENT})
        player = self._download_json(request, episode_id, 'Downloading player JSON')

        episode_type = player.get('typeOfEpisode')
        error_message = self._ERRORS.get(episode_type)
        if error_message:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_message), expected=True)

        formats = []
        video_url = player.get('urlVideo')
        if video_url:
            format_info = {
                'url': video_url,
                'format_id': 'http',
            }
            mobj = re.search(r'(?P<bitrate>\d+)K_(?P<width>\d+)x(?P<height>\d+)', video_url)
            if mobj:
                format_info.update({
                    'width': int_or_none(mobj.group('width')),
                    'height': int_or_none(mobj.group('height')),
                    'tbr': int_or_none(mobj.group('bitrate')),
                })
            formats.append(format_info)

        timestamp = int_or_none(self._download_webpage(
            self._TIME_API_URL,
            video_id, 'Downloading timestamp', fatal=False), 1000, time.time())
        timestamp_shifted = compat_str(timestamp + self._TIMESTAMP_SHIFT)
        token = hmac.new(
            self._MAGIC.encode('ascii'),
            (episode_id + timestamp_shifted).encode('utf-8'), hashlib.md5
        ).hexdigest()

        request = sanitized_Request(
            self._URL_VIDEO_TEMPLATE.format('windows', episode_id, timestamp_shifted, token),
            headers={'User-Agent': self._USER_AGENT})

        fmt_json = self._download_json(
            request, video_id, 'Downloading windows video JSON')

        result = fmt_json.get('resultDes')
        if result.lower() != 'ok':
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, result), expected=True)

        for format_id, video_url in fmt_json['resultObject'].items():
            if format_id == 'token' or not video_url.startswith('http'):
                continue
            if 'geodeswowsmpra3player' in video_url:
                # f4m_path = video_url.split('smil:', 1)[-1].split('free_', 1)[0]
                # f4m_url = 'http://drg.antena3.com/{0}hds/es/sd.f4m'.format(f4m_path)
                # this videos are protected by DRM, the f4m downloader doesn't support them
                continue
            video_url_hd = video_url.replace('free_es', 'es')
            formats.extend(self._extract_f4m_formats(
                video_url_hd[:-9] + '/manifest.f4m', video_id, f4m_id='hds',
                fatal=False))
            formats.extend(self._extract_mpd_formats(
                video_url_hd[:-9] + '/manifest.mpd', video_id, mpd_id='dash',
                fatal=False))
        self._sort_formats(formats)

        path_data = player.get('pathData')

        episode = self._download_xml(
            self._EPISODE_URL_TEMPLATE % path_data, video_id,
            'Downloading episode XML')

        duration = float_or_none(xpath_text(
            episode, './media/asset/info/technical/contentDuration', 'duration'))

        art = episode.find('./media/asset/info/art')
        title = xpath_text(art, './name', 'title')
        description = xpath_text(art, './description', 'description')
        thumbnail = xpath_text(episode, './media/asset/files/background', 'thumbnail')

        subtitles = {}
        subtitle_url = xpath_text(episode, './media/asset/files/subtitle', 'subtitle')
        if subtitle_url:
            subtitles['es'] = [{
                'ext': 'srt',
                'url': subtitle_url,
            }]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }

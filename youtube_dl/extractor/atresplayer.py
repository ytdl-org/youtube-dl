from __future__ import unicode_literals

import time
import hmac

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    int_or_none,
    float_or_none,
    xpath_text,
    ExtractorError,
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
                'thumbnail': 're:^https?://.*\.jpg$',
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

        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        error = self._html_search_regex(
            r'(?s)<ul class="list_error">(.+?)</ul>', response, 'error', default=None)
        if error:
            raise ExtractorError(
                'Unable to login: %s' % error, expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        episode_id = self._search_regex(
            r'episode="([^"]+)"', webpage, 'episode id')

        timestamp = int_or_none(self._download_webpage(
            self._TIME_API_URL,
            video_id, 'Downloading timestamp', fatal=False), 1000, time.time())
        timestamp_shifted = compat_str(timestamp + self._TIMESTAMP_SHIFT)
        token = hmac.new(
            self._MAGIC.encode('ascii'),
            (episode_id + timestamp_shifted).encode('utf-8')
        ).hexdigest()

        formats = []
        for fmt in ['windows', 'android_tablet']:
            request = compat_urllib_request.Request(
                self._URL_VIDEO_TEMPLATE.format(fmt, episode_id, timestamp_shifted, token))
            request.add_header('User-Agent', self._USER_AGENT)

            fmt_json = self._download_json(
                request, video_id, 'Downloading %s video JSON' % fmt)

            result = fmt_json.get('resultDes')
            if result.lower() != 'ok':
                raise ExtractorError(
                    '%s returned error: %s' % (self.IE_NAME, result), expected=True)

            for format_id, video_url in fmt_json['resultObject'].items():
                if format_id == 'token' or not video_url.startswith('http'):
                    continue
                if video_url.endswith('/Manifest'):
                    if 'geodeswowsmpra3player' in video_url:
                        f4m_path = video_url.split('smil:', 1)[-1].split('free_', 1)[0]
                        f4m_url = 'http://drg.antena3.com/{0}hds/es/sd.f4m'.format(f4m_path)
                        # this videos are protected by DRM, the f4m downloader doesn't support them
                        continue
                    else:
                        f4m_url = video_url[:-9] + '/manifest.f4m'
                    formats.extend(self._extract_f4m_formats(f4m_url, video_id))
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': 'android-%s' % format_id,
                        'preference': 1,
                    })
        self._sort_formats(formats)

        player = self._download_json(
            self._PLAYER_URL_TEMPLATE % episode_id,
            episode_id)

        path_data = player.get('pathData')

        episode = self._download_xml(
            self._EPISODE_URL_TEMPLATE % path_data,
            video_id, 'Downloading episode XML')

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

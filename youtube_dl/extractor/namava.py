# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
    url_or_none,
    str_or_none,
)


class NamavaIE(InfoExtractor):
    IE_NAME = 'namava'
    _NETRC_MACHINE = IE_NAME
    _VALID_URL = r'https?://(?:www\.)?play\.namava\.ir/.*\bm=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://play.namava.ir/?m=52396&p=desktop',
        'md5': '15639792543cc8e830a3451db1f44c72',
        'info_dict': {
            'id': '52396',
            'ext': 'mp4',
            'title': 'پلنگ صورتی - فصل ۴ قسمت ۱',
            'description': 'ماجراهای سرگرم‌کننده و طنز پلنگ صورتی و اتفاقات غیرمنتظره‌ای که همیشه برای او رخ می‌دهد و او با زیرکی خاص خودش، راه‌حلی را پیدا می‌کند و...'
        },
    }

    _LOGIN_URL = 'https://www.namava.ir/api/v1.0/accounts/by-phone/login'
    HOST = 'www.namava.ir'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()

        if not username:
            raise ExtractorError(
                'Unable to login: you have to pass username and password to logging in.',
                expected=True)

        login_data = {
            'UserName': username,
            'Password': password,
        }
        response = self._download_json(
            self._LOGIN_URL, None,
            'Logging in', data=urlencode_postdata(login_data))

        if response.get('succeeded') is True:
            self._set_cookie(self.HOST, 'auth_v2', response.get('result'))
            return True

        error = response.get('error', {})
        error_message = error.get('message', '')
        raise ExtractorError(
            'Unable to login: %s said: %s' % (self.IE_NAME, error_message),
            expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_json(
            'https://www.namava.ir/api2/movie/' + video_id,
            video_id, 'Fetching video info', headers={
                'Accept': 'application/json, text/plain, */*',
            })

        title = info.get('Name')
        if title is None:
            raise ExtractorError(
                'Unable to fetch video info',
                expected=True)

        media_info = info.get('MediaInfoModel', {})
        domain = media_info.get('Domain') or ''
        m3u8_file = media_info.get('File') or ''
        m3u8_url = url_or_none(domain + m3u8_file)

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', fatal=False)
        self._sort_formats(formats)

        url = formats[-1]['url']
        if len(formats) > 1:
            url = formats[-2]['url']

        result = {
            'id': video_id,
            'title': title,
            'ext': 'mp4',
            'description': str_or_none(info.get('ShortDescription')),
            'formats': formats,
            'thumbnail': url_or_none(info.get('ImageAbsoluteUrl')),
            'url': url
        }
        return result

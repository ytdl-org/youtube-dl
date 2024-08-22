from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    urlencode_postdata,
)


class TorrinsIE(InfoExtractor):
    IE_NAME = 'torrins'
    _VALID_URL = r'''(?x)
                    https?://
                        www\.torrins\.com/(?:guitar|piano|bass)-lessons/(?:song-lessons|style-genre)/[^/]+/(?P<id>[^/]+)/[^\.]+\.html
                    '''
    _LOGIN_URL = 'https://www.torrins.com/services/user/sign-in'
    _ORIGIN_URL = 'https://www.torrins.com'
    _NETRC_MACHINE = 'torrins'

    _TEST = {
        'url': 'https://www.torrins.com/guitar-lessons/song-lessons/english-songs/another-brick-in-the-wall/song-demo.html',
        'info_dict': {
            'id': 'another-brick-in-the-wall',
            'ext': 'mp4',
            'title': 'Another Brick in the Wall Guitar - Song Demo',
            'description': 'md5:c0d51f6f21ef4ec65f091055a5eef876',
            'duration': 579.29,
        },
        'skip': 'Requires torrins premium account credentials',
    }

    def _handle_error(self, response):
        if not isinstance(response, dict):
            return
        error = response['error']
        if error:
            error_str = 'Torrins returned error #%s: %s' % (error['code'], error.get['message'])
            error_data = error['data']
            if error_data:
                error_str += ' - %s' % error_data['formErrors']
            raise ExtractorError(error_str, expected=True)

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        def is_logged(reason):
            webpage = self._download_webpage(self._ORIGIN_URL, None, reason)

            return any(re.search(p, webpage) for p in (
                r'id=["\'](?:bt-logout)',
                r'>Logout<'))

        # already logged in
        if is_logged('Checking if already logged in'):
            return

        login_form = {
            'email': username,
            'password': password,
        }

        response = self._download_webpage(
            self._LOGIN_URL, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={
                'Referer': self._ORIGIN_URL,
                'Origin': self._ORIGIN_URL,
            })

        if not is_logged('Post login check'):
            error = self._html_search_regex(
                r'(?s)<div[^>]+class="form-errors[^"]*">(.+?)</div>',
                response, 'error message', default=None)
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_extract(self, url):
        course_id = self._match_id(url)

        webpage = self._download_webpage(url, course_id)

        video_json = self._html_search_regex(r"<div id=\"video\" idata='(.+?)'", webpage, 'video formats')
        video_json = self._parse_json(video_json, course_id)

        title = video_json.get('title') or self._og_search_title(webpage)
        video_id = video_json['id']

        formats = []

        for format, height in {'low': 240, 'medium': 360, 'high': 480}.items():
            if format in video_json:
                formats.append({
                    'url': video_json['low'],
                    'format_id': format,
                    'height': height,
                    'ext': 'mp4'
                })

        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }

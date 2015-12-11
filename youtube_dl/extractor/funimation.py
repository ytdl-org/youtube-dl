# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import (
    clean_html,
    determine_ext,
    encode_dict,
    sanitized_Request,
    ExtractorError,
    urlencode_postdata
)


class FunimationIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funimation\.com/shows/[^/]+/videos/official/(?P<id>[^?]+)'

    _TEST = {
        'url': 'http://www.funimation.com/shows/air/videos/official/breeze',
        'info_dict': {
            'id': '658',
            'display_id': 'breeze',
            'ext': 'mp4',
            'title': 'Air - 1 - Breeze',
            'description': 'md5:1769f43cd5fc130ace8fd87232207892',
            'thumbnail': 're:https?://.*\.jpg',
        },
    }

    def _download_webpage(self, url_or_request, video_id, note='Downloading webpage'):
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0',
        }
        if isinstance(url_or_request, compat_urllib_request.Request):
            for header, value in HEADERS.items():
                url_or_request.add_header(header, value)
        else:
            url_or_request = sanitized_Request(url_or_request, headers=HEADERS)
        response = super(FunimationIE, self)._download_webpage(url_or_request, video_id, note)
        return response

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        data = urlencode_postdata(encode_dict({
            'email_field': username,
            'password_field': password,
        }))
        login_request = sanitized_Request('http://www.funimation.com/login', data, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        login = self._download_webpage(
            login_request, None, 'Logging in as %s' % username)
        if re.search(r'<meta property="og:url" content="http://www.funimation.com/login"/>', login) is not None:
            raise ExtractorError('Unable to login, wrong username or password.', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        items = self._parse_json(
            self._search_regex(
                r'var\s+playersData\s*=\s*(\[.+?\]);\n',
                webpage, 'players data'),
            display_id)[0]['playlist'][0]['items']

        item = next(item for item in items if item.get('itemAK') == display_id)

        ERRORS_MAP = {
            'ERROR_MATURE_CONTENT_LOGGED_IN': 'matureContentLoggedIn',
            'ERROR_MATURE_CONTENT_LOGGED_OUT': 'matureContentLoggedOut',
            'ERROR_SUBSCRIPTION_LOGGED_OUT': 'subscriptionLoggedOut',
            'ERROR_VIDEO_EXPIRED': 'videoExpired',
            'ERROR_TERRITORY_UNAVAILABLE': 'territoryUnavailable',
            'SVODBASIC_SUBSCRIPTION_IN_PLAYER': 'basicSubscription',
            'SVODNON_SUBSCRIPTION_IN_PLAYER': 'nonSubscription',
            'ERROR_PLAYER_NOT_RESPONDING': 'playerNotResponding',
            'ERROR_UNABLE_TO_CONNECT_TO_CDN': 'unableToConnectToCDN',
            'ERROR_STREAM_NOT_FOUND': 'streamNotFound',
        }

        error_messages = {}
        video_error_messages = self._search_regex(
            r'var\s+videoErrorMessages\s*=\s*({.+?});\n',
            webpage, 'error messages', default=None)
        if video_error_messages:
            error_messages_json = self._parse_json(video_error_messages, display_id, fatal=False)
            if error_messages_json:
                for _, error in error_messages_json.items():
                    type_ = error.get('type')
                    description = error.get('description')
                    content = error.get('content')
                    if type_ == 'text' and description and content:
                        error_message = ERRORS_MAP.get(description)
                        if error_message:
                            error_messages[error_message] = content

        errors = []
        formats = []
        for video in item['videoSet']:
            auth_token = video.get('authToken')
            if not auth_token:
                continue
            funimation_id = video.get('FUNImationID') or video.get('videoId')
            if not auth_token.startswith('?'):
                auth_token = '?%s' % auth_token
            for quality in ('sd', 'hd', 'hd1080'):
                format_url = video.get('%sUrl' % quality)
                if not format_url:
                    continue
                if not format_url.startswith(('http', '//')):
                    errors.append(format_url)
                    continue
                if determine_ext(format_url) == 'm3u8':
                    m3u8_formats = self._extract_m3u8_formats(
                        format_url + auth_token, display_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=funimation_id or 'hls', fatal=False)
                    if m3u8_formats:
                        formats.extend(m3u8_formats)
                else:
                    formats.append({
                        'url': format_url + auth_token,
                    })

        if not formats and errors:
            raise ExtractorError(
                '%s returned error: %s'
                % (self.IE_NAME, clean_html(error_messages.get(errors[0], errors[0]))),
                expected=True)

        title = item['title']
        artist = item.get('artist')
        if artist:
            title = '%s - %s' % (artist, title)
        description = self._og_search_description(webpage) or item.get('description')
        thumbnail = self._og_search_thumbnail(webpage) or item.get('posterUrl')
        video_id = item.get('itemId') or display_id

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }

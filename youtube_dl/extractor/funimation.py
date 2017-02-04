# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urllib_parse_unquote_plus,
)
from ..utils import (
    clean_html,
    determine_ext,
    int_or_none,
    sanitized_Request,
    ExtractorError,
    urlencode_postdata
)


class FunimationIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funimation\.com/shows/[^/]+/videos/(?:official|promotional)/(?P<id>[^/?#&]+)'

    _NETRC_MACHINE = 'funimation'

    _TESTS = [{
        'url': 'http://www.funimation.com/shows/air/videos/official/breeze',
        'info_dict': {
            'id': '658',
            'display_id': 'breeze',
            'ext': 'mp4',
            'title': 'Air - 1 - Breeze',
            'description': 'md5:1769f43cd5fc130ace8fd87232207892',
            'thumbnail': r're:https?://.*\.jpg',
        },
        'skip': 'Access without user interaction is forbidden by CloudFlare, and video removed',
    }, {
        'url': 'http://www.funimation.com/shows/hacksign/videos/official/role-play',
        'info_dict': {
            'id': '31128',
            'display_id': 'role-play',
            'ext': 'mp4',
            'title': '.hack//SIGN - 1 - Role Play',
            'description': 'md5:b602bdc15eef4c9bbb201bb6e6a4a2dd',
            'thumbnail': r're:https?://.*\.jpg',
        },
        'skip': 'Access without user interaction is forbidden by CloudFlare',
    }, {
        'url': 'http://www.funimation.com/shows/attack-on-titan-junior-high/videos/promotional/broadcast-dub-preview',
        'info_dict': {
            'id': '9635',
            'display_id': 'broadcast-dub-preview',
            'ext': 'mp4',
            'title': 'Attack on Titan: Junior High - Broadcast Dub Preview',
            'description': 'md5:f8ec49c0aff702a7832cd81b8a44f803',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
        },
        'skip': 'Access without user interaction is forbidden by CloudFlare',
    }]

    _LOGIN_URL = 'http://www.funimation.com/login'

    def _download_webpage(self, *args, **kwargs):
        try:
            return super(FunimationIE, self)._download_webpage(*args, **kwargs)
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 403:
                response = ee.cause.read()
                if b'>Please complete the security check to access<' in response:
                    raise ExtractorError(
                        'Access to funimation.com is blocked by CloudFlare. '
                        'Please browse to http://www.funimation.com/, solve '
                        'the reCAPTCHA, export browser cookies to a text file,'
                        ' and then try again with --cookies YOUR_COOKIE_FILE.',
                        expected=True)
            raise

    def _extract_cloudflare_session_ua(self, url):
        ci_session_cookie = self._get_cookies(url).get('ci_session')
        if ci_session_cookie:
            ci_session = compat_urllib_parse_unquote_plus(ci_session_cookie.value)
            # ci_session is a string serialized by PHP function serialize()
            # This case is simple enough to use regular expressions only
            return self._search_regex(
                r'"user_agent";s:\d+:"([^"]+)"', ci_session, 'user agent',
                default=None)

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        data = urlencode_postdata({
            'email_field': username,
            'password_field': password,
        })
        user_agent = self._extract_cloudflare_session_ua(self._LOGIN_URL)
        if not user_agent:
            user_agent = 'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0'
        login_request = sanitized_Request(self._LOGIN_URL, data, headers={
            'User-Agent': user_agent,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        login_page = self._download_webpage(
            login_request, None, 'Logging in as %s' % username)
        if any(p in login_page for p in ('funimation.com/logout', '>Log Out<')):
            return
        error = self._html_search_regex(
            r'(?s)<div[^>]+id=["\']errorMessages["\'][^>]*>(.+?)</div>',
            login_page, 'error messages', default=None)
        if error:
            raise ExtractorError('Unable to login: %s' % error, expected=True)
        raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)

        errors = []
        formats = []

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

        USER_AGENTS = (
            # PC UA is served with m3u8 that provides some bonus lower quality formats
            ('pc', 'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0'),
            # Mobile UA allows to extract direct links and also does not fail when
            # PC UA fails with hulu error (e.g.
            # http://www.funimation.com/shows/hacksign/videos/official/role-play)
            ('mobile', 'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36'),
        )

        user_agent = self._extract_cloudflare_session_ua(url)
        if user_agent:
            USER_AGENTS = ((None, user_agent),)

        for kind, user_agent in USER_AGENTS:
            request = sanitized_Request(url)
            request.add_header('User-Agent', user_agent)
            webpage = self._download_webpage(
                request, display_id,
                'Downloading %s webpage' % kind if kind else 'Downloading webpage')

            playlist = self._parse_json(
                self._search_regex(
                    r'var\s+playersData\s*=\s*(\[.+?\]);\n',
                    webpage, 'players data'),
                display_id)[0]['playlist']

            items = next(item['items'] for item in playlist if item.get('items'))
            item = next(item for item in items if item.get('itemAK') == display_id)

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

            for video in item.get('videoSet', []):
                auth_token = video.get('authToken')
                if not auth_token:
                    continue
                funimation_id = video.get('FUNImationID') or video.get('videoId')
                preference = 1 if video.get('languageMode') == 'dub' else 0
                if not auth_token.startswith('?'):
                    auth_token = '?%s' % auth_token
                for quality, height in (('sd', 480), ('hd', 720), ('hd1080', 1080)):
                    format_url = video.get('%sUrl' % quality)
                    if not format_url:
                        continue
                    if not format_url.startswith(('http', '//')):
                        errors.append(format_url)
                        continue
                    if determine_ext(format_url) == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            format_url + auth_token, display_id, 'mp4', entry_protocol='m3u8_native',
                            preference=preference, m3u8_id='%s-hls' % funimation_id, fatal=False))
                    else:
                        tbr = int_or_none(self._search_regex(
                            r'-(\d+)[Kk]', format_url, 'tbr', default=None))
                        formats.append({
                            'url': format_url + auth_token,
                            'format_id': '%s-http-%dp' % (funimation_id, height),
                            'height': height,
                            'tbr': tbr,
                            'preference': preference,
                        })

        if not formats and errors:
            raise ExtractorError(
                '%s returned error: %s'
                % (self.IE_NAME, clean_html(error_messages.get(errors[0], errors[0]))),
                expected=True)

        self._sort_formats(formats)

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

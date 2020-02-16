# coding: utf-8
from __future__ import unicode_literals

import re

from .pornhub import PornHubBaseIE
from ..utils import ExtractorError
from ..utils import urlencode_postdata


class PornHubPremiumIE(PornHubBaseIE):
    """
    PornHubPremiumIE handles videos exclusively from pornhubpremium.com.
    """
    IE_NAME = 'pornhubpremium'
    IE_DESC = 'PornHub Premium'

    _NETRC_MACHINE = 'pornhubpremium'

    _HOST = 'pornhubpremium.com'
    _BASE_URL = 'https://%s' % _HOST
    _LOGIN_FORM_URL = 'https://%s/premium/login' % _HOST
    _LOGIN_POST_URL = 'https://www.%s/front/authenticate' % _HOST

    _VALID_URL = r'https?://(?P<host>(?:\w+?.)?pornhubpremium\.com)/(?:(?:view_video\.php\?viewkey=)|embed/)(?P<id>[\da-z]+)'

    @staticmethod
    def _is_authenticated(webpage):
        if '/user/logout' in webpage:
            return True
        if 'js_premiumLogOut' in webpage:
            return True
        return False

    def _login(self):
        username, password = self._get_login_info()

        if not username or not password:
            self.raise_login_required(
                'A \'%s\' account is required' % self._NETRC_MACHINE)

        # Set cookies
        self._set_cookie(self._HOST, 'age_verified', '1')
        self._set_cookie(self._HOST, 'platform', 'pc')

        # Verify our auth status
        main_page = self._download_webpage(
            self._BASE_URL, video_id=None, note='Verifying login', tries=1, fatal=False)

        # Already logged in
        if self._is_authenticated(main_page):
            return self.to_screen("Already authenticated")

        # Fetch login page
        login_page = self._download_webpage(
            self._LOGIN_FORM_URL, video_id=None, note='Logging in', tries=3, fatal=True)

        # Fetch login form
        login_form = self._hidden_inputs(login_page)
        login_form.update({
            'username': username,
            'password': password,
        })

        # Submit sign-in request
        response = self._download_json(
            self._LOGIN_POST_URL, video_id=None, note='Sending credentials', fatal=True,
            data=urlencode_postdata(login_form), headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self._LOGIN_POST_URL,
            })

        # Success
        if response.get('success') == '1':
            return self.to_screen("Successfully authenticated")

        # Error
        login_error = response.get('message')
        if login_error:
            raise ExtractorError('Unable to login: %s' % login_error, expected=True)
        self.report_warning('Login has probably failed')


class PornHubPremiumProfileIE(PornHubPremiumIE):
    """Extract videos from a model, pornstar, user, or channel profile."""

    IE_NAME = 'pornhubpremium:profile'

    _VALID_URL_PARTS = [
        r'https?://(?P<host>(?:\w+?.)?pornhubpremium\.com)/',
        r'(?:model|pornstar|users|channels)/(?P<username>[\w-]+)$'
    ]
    _VALID_URL = re.compile(''.join(_VALID_URL_PARTS))

    def _real_extract(self, url):
        self._set_cookies()
        return self.url_result('%s/videos' % url)


class PornHubPremiumProfileVideosIE(PornHubPremiumIE):
    """Extract videos from a model, pornstar, user, or channel profile."""

    IE_NAME = 'pornhubpremium:profile:videos'

    _VALID_URL_PARTS = [
        r'https?://(?P<host>(?:\w+?.)?pornhubpremium\.com)/',
        r'(?:model|pornstar|users|channels)/(?P<username>[\w-]+)/videos(?:/(?P<category>[\w-]+))?'
    ]
    _VALID_URL = re.compile(''.join(_VALID_URL_PARTS))

    def _real_extract(self, url):
        self._set_cookies()
        host, username, category = re.match(self._VALID_URL, url).groups()

        playlist_id = '%s-%s' % (username, category if category else 'videos')
        entries = self._extract_paged_entries(url, host, playlist_id)

        return self.playlist_result(entries, playlist_id)


class PornHubPremiumPlaylistIE(PornHubPremiumIE):
    """Extract videos from a playlist."""

    IE_NAME = 'pornhubpremium:playlist'
    _VALID_URL = r'https?://(?P<host>(?:\w+?.)?pornhubpremium\.com)/playlist/(?P<playlist_id>[\d]+)'

    def _real_extract(self, url):
        self._set_cookies()
        host, playlist_id = re.match(self._VALID_URL, url).groups()

        entries = self._extract_paged_entries(url, host, playlist_id)

        return self.playlist_result(
            entries, playlist_id, self._extract_playlist_title(url, playlist_id))

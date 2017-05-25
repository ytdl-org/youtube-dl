from __future__ import unicode_literals

import time
import re
from .jwplatform import JWPlatformBaseIE
from ..utils import (
    int_or_none,
    js_to_json,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class FetLifeIE(JWPlatformBaseIE):
    """InfoExtractor for fetlife.com"""

    _VALID_URL = r'https?://fetlife\.com/.*users/[0-9]+/videos/(?P<id>[0-9]+)'
    _LOGIN_URL = 'https://fetlife.com/users/sign_in'
    _NETRC_MACHINE = 'fetlife'

    _TESTS = [
        {
            'url': 'https://fetlife.com/users/1537262/videos/660686',
            'md5': '83ca9598d9c10afde75a4e730a882560',
            'info_dict': {
                'id': '660686',
                'thumbnail': r're:^https?://.*\.jpg\?token=[^\s]+$',
                'timestamp': 1484020451,
                'ext': 'mp4',
                'title': 'Sully Savage and Violet Monroe ',
                'uploader': 'BratPerversions',
                'uploader_id': '1537262',
                'age_limit': 18,
                'upload_date': '20170110',
                'duration': 91,
            },
            'params': {
                'usenetrc': True,
            },
        },
        {
            'url': 'https://fetlife.com/users/1972832/videos/672471',
            'md5': '4c01a6b57d099f82639f507298424073',
            'info_dict': {
                'id': '672471',
                'thumbnail': r're:^https?://.*\.jpg\?token=[^\s]+$',
                'timestamp': 1485368856,
                'ext': 'mp4',
                'title': '672471',
                'uploader': 'assman69415',
                'uploader_id': '1972832',
                'age_limit': 18,
                'upload_date': '20170125',
                'duration': 36,
            },
            'params': {
                'usenetrc': True,
            },
        },
        {
            'url': 'https://fetlife.com/explore/videos/#/users/3834660/videos/673702',
            'md5': 'b39d3ffa380aa01d8f1a62093bfe5f0d',
            'info_dict': {
                'id': '673702',
                'thumbnail': r're:^https?://.*\.jpg\?token=[^\s]+$',
                'timestamp': 1485518850,
                'ext': 'mp4',
                'title': 'Slap my tits',
                'uploader': 'Latexkittyxxx',
                'uploader_id': '3834660',
                'age_limit': 18,
                'upload_date': '20170127',
                'duration': 9,
            },
            'params': {
                'usenetrc': True,
            },
        },
    ]

    def _real_initialize(self):
        """log into fetlife.com"""

        (username, password) = self._get_login_info()
        if (username is None) or (password is None):
            raise ExtractorError('No login provided.', expected=True)
        webpage = self._download_webpage(self._LOGIN_URL, 'login')
        authenticity_token = self._search_regex(
            r'<input[^>]*?authenticity_token[^>]*?value="([^"]*)"[^>]/>',
            webpage, 'authenticity_token')

        login_form = {
            'utf8': '&#x2713;',
            'authenticity_token': authenticity_token,
            'user[otp_attempt]': 'step_1',
            'user[locale]': 'en',
            'user[login]': username,
            'user[password]': password,
        }

        request = sanitized_Request(
            self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Referer', self._LOGIN_URL)
        response = self._download_webpage(
            request, None, 'Logging in as {}'.format(username))

        if self._html_search_regex(r'Login to FetLife', response,
                                   'login error', default=None) is not None:
            raise ExtractorError(
                'Unable to login. Are username and password correct? Passwords are case sensitive.',
                expected=True)

        current_user = self._parse_json(
            self._search_regex(
                r'currentUser\s*=\s*({[^}]*})',
                response, 'user_info', default='{}'),
            username, transform_source=js_to_json)
        if current_user.get('isSupporter') is not None:
            if current_user.get('isSupporter') is False:
                raise ExtractorError('You need to be a fetlife supporter to see videos.', expected=True)

    def _real_extract(self, url):
        """extract information from fetlife.com"""

        video_id = self._match_id(url)
        url = re.sub(
            'https?://fetlife\.com/.*users/',
            'https://fetlife.com/users/', url)
        webpage = self._download_webpage(url, video_id)

        video_data = self._extract_jwplayer_data(
            webpage, video_id, require_title=False)

        uploader = self._search_regex(
            r'<div[^>]+class=[\'"]member-info[\'"]>[\s\S]+?<a[^>]+class=[\'"]nickname[\'"][\s\S]+?>([^<]+)',
            webpage, 'uploader', default=None)
        uploader_id = self._search_regex(
            r'<div[^>]+class=[\'"]member-info[\'"]>[\s\S]+?<a[^>]+href=[\'"]/users/([0-9]+)',
            webpage, 'uploader_id', default=None)

        timeiso = self._search_regex(
            r'<section[^>]+id=[\'"]video_caption[\'"]>[\s\S]+?<time[^>]+datetime\s*=\s*[\'"]([^<]+?)[\'"]',
            webpage, 'timestamp', default=None)
        if timeiso:
            timestamp = int_or_none(
                time.mktime(time.strptime(timeiso, "%Y-%m-%dT%H:%M:%SZ")))
        else:
            timestamp = None

        if video_data.get('title') is None:
            title = self._search_regex(
                r'<section[^>]+id=[\'"]video_caption[\'"]>[^<]*?<div[^>]+id\s*=\s*[\'"]title_description_credits[\'"][^>]*>[^<]*(?:(?:<p[^>]+class\s*=\s*[\'"]description[\'"][^>]*>)|(?:<h1>))([^<]+)',
                webpage, 'title', default=video_id)

        mobj = re.search(
            r'clock<[^>]*>\s*(?P<duration_minutes>[0-9]+)m\s*(?P<duration_seconds>[0-9]+)s',
            webpage)
        if mobj is not None:
            duration_minutes = int_or_none(
                mobj.groupdict().get('duration_minutes'))
            duration_seconds = int_or_none(
                mobj.groupdict().get('duration_seconds'))
            if (duration_minutes is not None) and (duration_seconds is not None):
                duration = duration_minutes * 60 + duration_seconds

        like_count = int_or_none(
            self._search_regex(
                r'[0-9]+\s*Love\s*it',
                webpage, 'like_count', default=None))

        video_data.update({
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'age_limit': 18,
            'duration': duration,
            'like_count': like_count,
        })

        return video_data

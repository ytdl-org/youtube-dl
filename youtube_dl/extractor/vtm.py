from __future__ import unicode_literals

import re

from .generic import GenericIE
from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    compat_urllib_parse_urlencode,
    ExtractorError,
    remove_end,
)


class VTMIE(InfoExtractor):
    """Download full episodes that require an account from vtm.be or q2.be.

    The generic extractor can be used to download clips that do no require an
    account.
    """
    _VALID_URL = r'https?://(?:www\.)?(?P<site_id>vtm|q2)\.be/video[/?].+?'
    _NETRC_MACHINE = 'vtm'
    _APIKEY = '3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-'
    _TESTS = [
        {
            'url': 'http://vtm.be/video/volledige-afleveringen/id/vtm_20170219_VM0678361_vtmwatch',
            'info_dict': {
                'id': 'vtm_20170219_VM0678361_vtmwatch',
                'ext': 'mp4',
                'title': 'Allemaal Chris afl. 6',
                'description': 'md5:4be86427521e7b07e0adb0c9c554ddb2',
            },
            'skip_download': True,
        },
        {
            'url': 'http://vtm.be/video/volledige-afleveringen/id/257107153551000',
            'only_matching': True,
        },
        {
            'url': 'http://vtm.be/video?aid=163157',
            'only_matching': True,
        },
        {
            'url': 'http://www.q2.be/video/volledige-afleveringen/id/2be_20170301_VM0684442_q2',
            'only_matching': True,
        },
        {
            'url': 'http://vtm.be/video?aid=168332',
            'info_dict': {
                'id': 'video?aid=168332',
                'ext': 'mp4',
                'title': 'Videozone',
            },
        },
    ]

    def _real_initialize(self):
        self._logged_in = False

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None or password is None:
            self.raise_login_required()

        auth_data = {
            'APIKey': self._APIKEY,
            'sdk': 'js_6.1',
            'format': 'json',
            'loginID': username,
            'password': password,
        }

        auth_info = self._download_json(
            'https://accounts.eu1.gigya.com/accounts.login', None,
            note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata(auth_data), fatal=True)

        error_message = auth_info.get('errorDetails')
        if error_message:
            raise ExtractorError(
                'Unable to login: %s' % error_message, expected=True)

        self._uid = auth_info['UID']
        self._uid_signature = auth_info['UIDSignature']
        self._signature_timestamp = auth_info['signatureTimestamp']

        self._logged_in = True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id = mobj.group('site_id')

        webpage = self._download_webpage(url, None, "Downloading webpage")

        # The URL sometimes contains the video id, but not always, e.g., test
        # case 3. Fortunately, all webpages of videos requiring authentication
        # contain the video id.
        video_id = self._search_regex(
            r'\\"vodId\\":\\"(.+?)\\"', webpage, 'video_id', default=None)

        # It was most likely a video not requiring authentication.
        if not video_id:
            return self.url_result(url, 'Generic')

        if not self._logged_in:
            self._login()

        title = self._html_search_regex(
            r'\\"title\\":\\"(.+?)\\"', webpage, 'title', default=None)

        description = self._html_search_regex(
            r'<div[^>]+class="field-item\s+even">\s*<p>(.+?)</p>',
            webpage, 'description', default=None)

        data_url = 'http://vod.medialaan.io/api/1.0/item/%s/video' % video_id
        m3u8_data = {
            'app_id': 'vtm_watch' if site_id == 'vtm' else 'q2',
            'user_network': 'vtm-sso',
            'UID': self._uid,
            'UIDSignature': self._uid_signature,
            'signatureTimestamp': self._signature_timestamp,
        }
        data = self._download_json(data_url, video_id, query=m3u8_data)

        formats = self._extract_m3u8_formats(
            data['response']['uri'], video_id, entry_protocol='m3u8_native',
            ext='mp4', m3u8_id='hls')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }

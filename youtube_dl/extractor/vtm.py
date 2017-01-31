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
            'md5': '9357926318cdfcb10079d85d56f4e04e',
            'info_dict': {
                'id': 'vtm_20170219_VM0678361_vtmwatch',
                'ext': 'mp4',
                'title': 'Allemaal Chris afl. 6',
                'description': 'md5:4be86427521e7b07e0adb0c9c554ddb2',
            },
            'skip_download': True,
        }
    ]

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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id = mobj.group('site_id')

        webpage = self._download_webpage(url, None)

        # There are two known types of URLs both pointing to the same video.
        # The type of URL you get depends on how you navigate to the video.
        # Unfortunately, only one type of URL contains the actual video id:
        #
        # http://vtm.be/video/volledige-afleveringen/id/257059160170000
        #
        # The video id can also be something like:
        # "vtm_20170213_VM0678492_vtmwatch"
        #
        # The other type of URL looks like:
        #
        # http://vtm.be/video?aid=166380
        #
        # The 'aid' is not the video id we are looking for. There can also be
        # a lot of very long parameters in addition to the 'aid' parameter.
        #
        # So to work in all cases, we extract the video_id from the webpage
        # instead of the URL.
        video_id = self._search_regex(
            r'\\"vodId\\":\\"(.+?)\\"', webpage, 'video_id', default=None)

        # When no video_id is found, it was most likely a video not requiring
        # authentication, so just fall back to the generic extractor
        if not video_id:
            return self.url_result(url, 'Generic')

        self._login()

        title = remove_end(self._og_search_title(webpage), ' - Volledige Afleveringen')

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

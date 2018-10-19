# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
    urlencode_postdata,
)


class HiDiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hidive\.com/stream/(?P<title>[^/]+)/(?P<key>[^/?#&]+)'
    # Using X-Forwarded-For results in 403 HTTP error for HLS fragments,
    # so disabling geo bypass completely
    _GEO_BYPASS = False
    _NETRC_MACHINE = 'hidive'
    _LOGIN_URL = 'https://www.hidive.com/account/login'

    _TESTS = [{
        'url': 'https://www.hidive.com/stream/the-comic-artist-and-his-assistants/s01e001',
        'info_dict': {
            'id': 'the-comic-artist-and-his-assistants/s01e001',
            'ext': 'mp4',
            'title': 'the-comic-artist-and-his-assistants/s01e001',
            'series': 'the-comic-artist-and-his-assistants',
            'season_number': 1,
            'episode_number': 1,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires Authentication',
    }]

    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            return

        webpage = self._download_webpage(self._LOGIN_URL, None, 'Login page')
        form = self._search_regex(
            r'(?s)<form[^>]+action="/account/login"[^>]*>(.+?)</form>',
            webpage, 'login form')
        data = self._hidden_inputs(form)
        data.update({
            'Email': email,
            'Password': password,
        })
        self._download_webpage(
            self._LOGIN_URL, None, 'Logging in', data=urlencode_postdata(data))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title, key = mobj.group('title', 'key')
        video_id = '%s/%s' % (title, key)

        # Need to choose a profile to reach stream page
        webpage = self._download_webpage('https://www.hidive.com/profile/choose', None, 'Getting profiles')
        profile_id = self._search_regex(r'<button[^>]+data-profile-id="([0-9A-z]+)[^>]+>', webpage, 'Profile id')
        profile_hash = self._search_regex(r'<button[^>]+data-hash="([0-9A-z]+)[^>]+>', webpage, 'Profile hash')

        profile_data = {
            'profileId': profile_id,
            'hash': profile_hash
        }

        # PlayerId is subject to change, can grab the valid id from the stream page
        self._download_webpage('https://www.hidive.com/ajax/chooseprofile', None, 'Choosing first profile', data=urlencode_postdata(profile_data))
        webpage = self._download_webpage(url, None, 'Getting PlayerId')
        json_data = self._parse_json(self._html_search_regex(r'<body data-json=\'(.+)\'>', webpage, 'Player settings'), video_id)

        settings = self._download_json(
            'https://www.hidive.com/play/settings', video_id,
            data=urlencode_postdata({
                'Title': title,
                'Key': key,
                'PlayerId': json_data['playerConfig']['PlayerId']
            }))

        restriction = settings.get('restrictionReason')
        if restriction == 'RegionRestricted':
            self.raise_geo_restricted()

        if restriction and restriction != 'None':
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, restriction), expected=True)

        formats = []
        subtitles = {}
        for rendition_id, rendition in settings['renditions'].items():
            bitrates = rendition.get('bitrates')
            if not isinstance(bitrates, dict):
                continue
            m3u8_url = url_or_none(bitrates.get('hls'))
            if not m3u8_url:
                continue
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='%s-hls' % rendition_id, fatal=False))
            cc_files = rendition.get('ccFiles')
            if not isinstance(cc_files, list):
                continue
            for cc_file in cc_files:
                if not isinstance(cc_file, list) or len(cc_file) < 3:
                    continue
                cc_lang = cc_file[0]
                cc_url = url_or_none(cc_file[2])
                if not isinstance(cc_lang, compat_str) or not cc_url:
                    continue
                subtitles.setdefault(cc_lang, []).append({
                    'url': cc_url,
                })
        self._sort_formats(formats)

        season_number = int_or_none(self._search_regex(
            r's(\d+)', key, 'season number', default=None))
        episode_number = int_or_none(self._search_regex(
            r'e(\d+)', key, 'episode number', default=None))

        return {
            'id': video_id,
            'title': video_id,
            'subtitles': subtitles,
            'formats': formats,
            'series': title,
            'season_number': season_number,
            'episode_number': episode_number,
        }

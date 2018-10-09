# coding: utf-8
from __future__ import unicode_literals

import re
import requests
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    strip_or_none,
    unescapeHTML,
    urlencode_postdata,
)
from datetime import datetime


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://auth.roosterteeth.com/oauth/token'
    _OAUTH_TOKEN = None

    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '9156',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'description': 'md5:0cc3b21986d54ed815f5faeccd9a9ca5',
            'thumbnail': r're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': '10',
            'comment_count': int,
        },
    }, {
        'url': 'http://achievementhunter.roosterteeth.com/episode/off-topic-the-achievement-hunter-podcast-2016-i-didn-t-think-it-would-pass-31',
        'only_matching': True,
    }, {
        'url': 'http://funhaus.roosterteeth.com/episode/funhaus-shorts-2016-austin-sucks-funhaus-shorts',
        'only_matching': True,
    }, {
        'url': 'http://screwattack.roosterteeth.com/episode/death-battle-season-3-mewtwo-vs-shadow',
        'only_matching': True,
    }, {
        'url': 'http://theknow.roosterteeth.com/episode/the-know-game-news-season-1-boring-steam-sales-are-better',
        'only_matching': True,
    }, {
        # only available for FIRST members
        'url': 'http://roosterteeth.com/episode/rt-docs-the-world-s-greatest-head-massage-the-world-s-greatest-head-massage-an-asmr-journey-part-one',
        'only_matching': True,
    }]

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        pattern = "REACT_APP_AUTH_CLIENT_ID: rtConfigSetup\('(4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5)'"
        client_page = self._download_webpage(
            'https://roosterteeth.com', None,
            note='Getting client id',
            errnote='Unable to download client info.')
        client_id = re.findall(pattern, client_page)[0]

        login_data = {
            'username': username,
            'password': password,
            'client_id': client_id,
            'scope': 'user public',
            'grant_type': 'password',
        }
        response = requests.post(self._LOGIN_URL, data=login_data)

        try:
            self._OAUTH_TOKEN = response.json()['access_token']
        except KeyError:
            raise self.raise_login_required("Login required.")
        return

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        headers = self.geo_verification_headers()

        if self._OAUTH_TOKEN:
            headers['authorization'] = 'Bearer %s' % self._OAUTH_TOKEN
        print('https://svod-be.roosterteeth.com/api/v1/episodes/%s' % display_id)
        video_info = self._download_json('https://svod-be.roosterteeth.com/api/v1/episodes/%s' % display_id,
                                         display_id, note='m3u8', headers=headers)
        sponsor_only = video_info['data'][0]['attributes']['is_sponsors_only']

        if sponsor_only and not self._OAUTH_TOKEN:
            self.raise_login_required("Video is for sponsors only.  Log in with an account")

        public_dt = datetime.strptime(video_info['data'][0]['attributes']['public_golive_at'], '%Y-%m-%dT%H:%M:%S.000Z')

        if (public_dt.timestamp() >= time.time()) and not self._OAUTH_TOKEN:
            self.raise_login_required("Video not yet available for free members.  Log in with an account")

        stream_info = self._download_json('https://svod-be.roosterteeth.com/api/v1/episodes/%s/videos' % display_id,
                                          display_id, note='m3u8', headers=headers)
        m3u8_url = stream_info['data'][0]['attributes']['url']
        title = video_info['data'][0]['attributes']['title']
        season = video_info['data'][0]['attributes']['season_number']
        episode = video_info['data'][0]['attributes']['number']
        description = video_info['data'][0]['attributes']['description']
        series = video_info['data'][0]['attributes']['show_title']
        thumbnail = video_info['data'][0]['included']['images'][0]['attributes']['thumb']
        video_id = str(video_info['data'][0]['id'])
        comment_count = 0

        if not m3u8_url:
            raise ExtractorError('Unable to extract m3u8 URL')

        formats = self._extract_m3u8_formats(m3u8_url, display_id, ext='mp4',
                                             entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'series': series,
            'episode': str(episode),
            'comment_count': comment_count,
            'formats': formats,
        }


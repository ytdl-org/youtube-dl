# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    try_get,
    str_or_none,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/(?:episode|watch)/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://auth.roosterteeth.com/oauth/token'
    _ACCESS_TOKEN = None
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '9156',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'description': 'md5:168a54b40e228e79f4ddb141e89fe4f5',
            'thumbnail': r're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': 'Million Dollars, But... The Game Announcement',
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
    }, {
        'url': 'https://roosterteeth.com/watch/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'only_matching': True,
    }]

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        cookie = self._get_cookie('rt_access_token')
        if cookie and not cookie.is_expired():
            self._ACCESS_TOKEN = cookie.value
            return

        response = self._download_json(
            self._LOGIN_URL, None,
            note='Logging in',
            errnote='Unable to log in',
            data=urlencode_postdata({
                'username': username,
                'password': password,
                'client_id': '4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5',
                'grant_type': 'password',
            })
        )

        self._ACCESS_TOKEN = response.get('access_token')
        if not self._ACCESS_TOKEN:
            raise ExtractorError('Unable to log in')

        created_at = response.get('created_at', 0)
        expires_in = response.get('expires_in', 0)

        self._set_cookie('.roosterteeth.com', 'rt_access_token', self._ACCESS_TOKEN, created_at + expires_in)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = 'https://svod-be.roosterteeth.com/api/v1/episodes/%s' % display_id

        headers = {}
        if self._ACCESS_TOKEN:
            headers['Authorization'] = 'Bearer ' + self._ACCESS_TOKEN

        try:
            m3u8_url = self._download_json(
                api_episode_url + '/videos', display_id,
                'Downloading video JSON metadata', headers=headers)['data'][0]['attributes']['url']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                if self._parse_json(e.cause.read().decode(), display_id).get('access') is False:
                    self.raise_login_required(
                        '%s is only available for FIRST members' % display_id)
            raise

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        episode = self._download_json(
            api_episode_url, display_id,
            'Downloading episode JSON metadata', headers=headers)['data'][0]
        attributes = episode['attributes']
        title = attributes.get('title') or attributes['display_title']
        video_id = compat_str(episode['id'])

        thumbnails = []
        for i, size in enumerate(['thumb', 'small', 'medium', 'large']):
            thumbnail = try_get(episode, lambda x: x['included']['images'][0]['attributes'][size], compat_str)
            if thumbnail:
                thumbnails.append({'url': thumbnail, 'id': i})

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': attributes.get('description') or attributes.get('caption'),
            'thumbnails': thumbnails,
            'series': attributes.get('show_title'),
            'season_number': int_or_none(attributes.get('season_number')),
            'season_id': attributes.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(attributes.get('number')),
            'episode_id': str_or_none(episode.get('uuid')),
            'formats': formats,
            'channel_id': attributes.get('channel_id'),
            'duration': int_or_none(attributes.get('length')),
        }

    def _get_cookie(self, name):
        for cookie in self._downloader.cookiejar:
            if cookie.name == name:
                return cookie
        return None

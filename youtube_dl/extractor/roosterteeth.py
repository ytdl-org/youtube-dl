# coding: utf-8
from __future__ import unicode_literals

import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_str,
    str_or_none,
    try_get,
    unified_timestamp,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://auth.roosterteeth.com/oauth/token'
    _API_URL = 'https://svod-be.roosterteeth.com/api/v1/episodes/'
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
            'description': 'md5:0cc3b21986d54ed815f5faeccd9a9ca5',
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
    }]

    def _login(self):
        (username, password) = self._get_login_info()
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

        headers = {}
        if self._ACCESS_TOKEN:
            headers['Authorization'] = 'Bearer ' + self._ACCESS_TOKEN

        api_response = self._call_api(
            display_id,
            note='Downloading video information (1/2)',
            errnote='Unable to download video information (1/2)',
            headers=headers,
        )

        data = api_response['data'][0]

        attributes = data['attributes']
        episode = attributes.get('display_title')
        title = attributes['title']
        description = attributes.get('caption')
        series = attributes.get('show_title')

        thumbnails = []
        for i, size in enumerate(['thumb', 'small', 'medium', 'large']):
            thumbnail = try_get(data, lambda x: x['included']['images'][0]['attributes'][size], compat_str)
            if thumbnail:
                thumbnails.append({'url': thumbnail, 'id': i})

        video_response = self._call_api(
            display_id,
            path='/videos',
            note='Downloading video information (2/2)',
            errnote='Unable to download video information (2/2)',
            headers=headers,
        )

        if video_response.get('access') is not None:
            now = time.time()
            sponsor_golive = unified_timestamp(attributes.get('sponsor_golive_at'))
            member_golive = unified_timestamp(attributes.get('member_golive_at'))
            public_golive = unified_timestamp(attributes.get('public_golive_at'))

            if attributes.get('is_sponsors_only', False):
                if now < sponsor_golive:
                    self._golive_error(display_id, 'FIRST members')
                else:
                    self.raise_login_required('{0} is only available for FIRST members'.format(display_id))
            else:
                if now < member_golive:
                    self._golive_error(display_id, 'site members')
                elif now < public_golive:
                    self._golive_error(display_id, 'the public')
                else:
                    raise ExtractorError('Video is not available')

        video_attributes = try_get(video_response, lambda x: x['data'][0]['attributes'])

        m3u8_url = video_attributes.get('url')
        if not m3u8_url:
            raise ExtractorError('Unable to extract m3u8 URL')

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        video_id = str_or_none(video_attributes.get('content_id'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'series': series,
            'episode': episode,
            'formats': formats,
        }

    def _golive_error(self, video_id, member_level):
        raise ExtractorError('{0} is not yet live for {1}'.format(video_id, member_level))

    def _call_api(self, video_id, path=None, **kwargs):
        url = self._API_URL + video_id
        if path:
            url = url + path

        return self._download_json(url, video_id, **kwargs)

    def _get_cookie(self, name):
        for cookie in self._downloader.cookiejar:
            if cookie.name == name:
                return cookie
        return None

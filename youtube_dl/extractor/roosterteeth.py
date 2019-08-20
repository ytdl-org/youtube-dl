# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/(?:episode|watch)/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://roosterteeth.com/login'
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

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='Unable to download login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'username': username,
            'password': password,
        })

        login_request = self._download_webpage(
            self._LOGIN_URL, None,
            note='Logging in',
            data=urlencode_postdata(login_form),
            headers={
                'Referer': self._LOGIN_URL,
            })

        if not any(re.search(p, login_request) for p in (
                r'href=["\']https?://(?:www\.)?roosterteeth\.com/logout"',
                r'>Sign Out<')):
            error = self._html_search_regex(
                r'(?s)<div[^>]+class=(["\']).*?\balert-danger\b.*?\1[^>]*>(?:\s*<button[^>]*>.*?</button>)?(?P<error>.+?)</div>',
                login_request, 'alert', default=None, group='error')
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = 'https://svod-be.roosterteeth.com/api/v1/episodes/%s' % display_id

        try:
            m3u8_url = self._download_json(
                api_episode_url + '/videos', display_id,
                'Downloading video JSON metadata')['data'][0]['attributes']['url']
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
            'Downloading episode JSON metadata')['data'][0]
        attributes = episode['attributes']
        title = attributes.get('title') or attributes['display_title']
        video_id = compat_str(episode['id'])

        thumbnails = []
        for image in episode.get('included', {}).get('images', []):
            if image.get('type') == 'episode_image':
                img_attributes = image.get('attributes') or {}
                for k in ('thumb', 'small', 'medium', 'large'):
                    img_url = img_attributes.get(k)
                    if img_url:
                        thumbnails.append({
                            'id': k,
                            'url': img_url,
                        })

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

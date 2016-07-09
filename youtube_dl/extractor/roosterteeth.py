# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://roosterteeth.com/login'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'info_dict': {
            'id': '26576',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 'Introducing Million Dollars, But... The Game! Available for pre-order now at www.MDBGame.com ',
            'creator': 'Rooster Teeth',
            'series': 'Million Dollars, But...',
            'episode': 'Million Dollars, But... The Game Announcement',
            'episode_id': '26576',
        },
        'params': {
            'skip_download': True,  # m3u8 downloads
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
    }]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None or password is None:
            return False

        # token is required to authenticate request
        login_page = self._download_webpage(self._LOGIN_URL, None, 'Getting login token', 'Unable to get login token')

        login_form = self._hidden_inputs(login_page)
        login_form.update({
            'username': username,
            'password': password,
        })
        login_payload = urlencode_postdata(login_form)

        # required for proper responses
        login_headers = {
            'Referer': self._LOGIN_URL,
        }

        login_request = self._download_webpage(
            self._LOGIN_URL, None,
            note='Logging in as %s' % username,
            data=login_payload,
            headers=login_headers)

        if 'Authentication failed' in login_request:
            raise ExtractorError(
                'Login failed (invalid username/password)', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        match_id = self._match_id(url)
        webpage = self._download_webpage(url, match_id)

        episode_id = self._html_search_regex(r"commentControls\('#comment-([0-9]+)'\)", webpage, 'episode id', match_id, False)

        self.report_extraction(episode_id)

        title = self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'episode title', self._og_search_title(webpage), False)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        creator = self._html_search_regex(r'<h3>Latest (.+) Gear</h3>', webpage, 'site', 'Rooster Teeth', False)
        series = self._html_search_regex(r'<h2>More ([^<]+)</h2>', webpage, 'series', fatal=False)
        episode = self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'episode title', fatal=False)

        if '<div class="non-sponsor">' in webpage:
            self.raise_login_required('%s is only available for FIRST members' % title)

        if '<div class="golive-gate">' in webpage:
            self.raise_login_required('%s is not available yet' % title)

        formats = self._extract_m3u8_formats(self._html_search_regex(r"file: '(.+?)m3u8'", webpage, 'm3u8 url') + 'm3u8', episode_id, ext='mp4')
        self._sort_formats(formats)

        return {
            'id': episode_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'creator': creator,
            'series': series,
            'episode': episode,
            'episode_id': episode_id,
        }

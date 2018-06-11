# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    urlencode_postdata,
)

class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://roosterteeth.com/login'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '26576',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But...: Million Dollars, But... The Game Announcement',
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

        try:
            json_m3u8 = self._download_json(
                'https://svod-be.roosterteeth.com/api/v1/episodes/%s/videos' % display_id,
                display_id, 'Downloading JSON m3u8')
            json_metadata = self._download_json(
                'https://svod-be.roosterteeth.com/api/v1/episodes/%s/' % display_id,
                display_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                self.raise_login_required('This video is only available for FIRST memebers')
            raise

        try:
            m3u8_url = json_m3u8['data'][0]['attributes']['url']
        except:
            raise ExtractorError('Unable to extract m3u8 URL')

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)
        
        json_body = json_metadata['data'][0]
        json_attributes = json_body['attributes']
        
        display_title = json_attributes['display_title']
        
        title = str_or_none(self._search_regex(r': ([\w]+)$', display_title, 'title'))
        episode = int_or_none(self._search_regex(r':E([\d]+)', display_title, 'episode', fatal=False))
        season = int_or_none(self._search_regex(r'^V([\d]+):E', display_title, 'season', fatal=False))
        
        video_id = str(json_body.get('id'))
        thumbnail = json_body['included']['images'][0]['attributes']['large']
        description = json_attributes.get('description')
        series = json_attributes.get('show_title')
        
        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'series': series,
            'season': season,
            'episode': episode,
            'formats': formats,
        }

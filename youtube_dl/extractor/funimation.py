# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
    ExtractorError,
    urlencode_postdata
)
import re

class FunimationCommonIE(InfoExtractor):
    _NETRC_MACHINE = 'funimation'
    _TOKEN = None

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        try:
            data = self._download_json(
                'https://prod-api-funimationnow.dadcdigital.com/api/auth/login/',
                None, 'Logging in as %s' % username, data=urlencode_postdata({
                    'username': username,
                    'password': password,
                }))
            self._TOKEN = data['token']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                error = self._parse_json(e.cause.read().decode(), None)['error']
                raise ExtractorError(error, expected=True)
            raise

    def _real_initialize(self):
        self._login()

class FunimationIE(FunimationCommonIE):
    _VALID_URL = r'https?://(?:www\.)?funimation(?:\.com|now\.uk)/shows/[^/]+/'+\
                 r'(?P<id>[^/?#&]+)/?(?P<alpha>simulcast|uncut)?/?(?:\?lang=(?P<lang>english|japanese))?'

    _TESTS = [{
        'url': 'https://www.funimation.com/shows/hacksign/role-play/',
        'info_dict': {
            'id': '91144',
            'display_id': 'role-play',
            'ext': 'mp4',
            'title': '.hack//SIGN - Role Play',
            'description': 'md5:b602bdc15eef4c9bbb201bb6e6a4a2dd',
            'thumbnail': r're:https?://.*\.jpg',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.funimation.com/shows/attack-on-titan-junior-high/broadcast-dub-preview/',
        'info_dict': {
            'id': '210051',
            'display_id': 'broadcast-dub-preview',
            'ext': 'mp4',
            'title': 'Attack on Titan: Junior High - Broadcast Dub Preview',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.funimationnow.uk/shows/puzzle-dragons-x/drop-impact/simulcast/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        m = re.compile(self._VALID_URL).match(url)
        display_id = m.group('id')
        intended_alpha = m.group('alpha') or 'simulcast'
        intended_language = m.group('lang') or 'english'
        webpage = self._download_webpage(url, display_id)

        def _search_kane(name):
            return self._search_regex(
                r"KANE_customdimensions\.%s\s*=\s*'([^']+)';" % name,
                webpage, name, default=None)

        title_data = self._parse_json(self._search_regex(
            r'TITLE_DATA\s*=\s*({[^}]+})',
            webpage, 'title data', default=''),
            display_id, js_to_json, fatal=False) or {}

        video_id = title_data.get('id') or self._search_regex([
            r"KANE_customdimensions.videoID\s*=\s*'(\d+)';",
            r'<iframe[^>]+src="/player/(\d+)"',
        ], webpage, 'video_id', default=None)
        if not video_id:
            player_url = self._html_search_meta([
                'al:web:url',
                'og:video:url',
                'og:video:secure_url',
            ], webpage, fatal=True)
            video_id = self._search_regex(r'/player/(\d+)', player_url, 'video id')

        try:
            headers = {}
            if self._TOKEN:
                headers['Authorization'] = 'Token %s' % self._TOKEN
            experience = self._download_json(
                'https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/title/experience/%s/' % video_id,
                video_id, headers=headers)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error = self._parse_json(e.cause.read(), video_id)['errors'][0]
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error.get('detail') or error.get('title')), expected=True)
            raise
        showLanguage = _search_kane('showLanguage')
        alpha = title_data['alpha'].lower()
        target_video_id = int(video_id)
        matched_episode = None
        for season in experience['seasons']:
            for episode in season['episodes']:
                # We can use showLanguage to know what the video_id is expected to be, let's look for it
                desiredcut = episode['languages'].get(showLanguage, {'alpha': {}})
                desiredcut = desiredcut['alpha'].get(alpha, {})
                if desiredcut.get('experienceId', None) == target_video_id:
                    # Winning!
                    matched_episode = episode
                    break
            if matched_episode:
                break
        if not matched_episode:
            raise ExtractorError('%s said: Failed to find the episode' % (
                    self.IE_NAME), expected=False)
        matched_alpha = None
        matched_language = None
        # Preferences
        for il in [intended_language, 'english', 'japanese']:
            if (il in episode['languages']):
                for ia in [intended_alpha, 'uncut', 'simulcast', 'extras']:
                    if (ia in episode['languages'][il]['alpha'] and
                        episode['languages'][il]['alpha'][ia]['sources']):
                        matched_language = il
                        matched_alpha = ia
                        break
            if (matched_alpha):
                break
        if not matched_alpha:
            raise ExtractorError('%s could not find acceptable language and alpha'%self.IE_NAME, expected=False)
        if matched_language != intended_language:
            print("Falling back to %s"%matched_language)
        if matched_alpha != intended_alpha:
            print("Falling back to %s"%matched_alpha)
        intended_language = matched_language
        intended_alpha = matched_alpha
        final_alpha = episode['languages'][intended_language]['alpha'][intended_alpha]
        video_id = str(final_alpha['experienceId'])
        try:
            headers = {}
            if self._TOKEN:
                headers['Authorization'] = 'Token %s' % self._TOKEN
            sources = self._download_json(
                'https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/video/%s/signed/' % video_id,
                video_id, headers=headers)['items']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error = self._parse_json(e.cause.read(), video_id)['errors'][0]
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error.get('detail') or error.get('title')), expected=True)
            raise
        formats = []
        for source in sources:
            source_url = source.get('src')
            if not source_url:
                continue
            source_type = source.get('videoType') or determine_ext(source_url)
            if source_type == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'format_id': source_type,
                    'url': source_url,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': "%s - %s"%(experience['showTitle'], episode['episodeTitle']),
            'description': episode['episodeSummary'],
            'thumbnail': self._og_search_thumbnail(webpage),
            'series': experience['showTitle'],
            'season_number': int_or_none(season['seasonId']),
            'episode_number': int_or_none(episode['episodeId']),
            'episode': episode['episodeTitle'],
            'season_id': experience['showId'],
            'formats': formats,
            'duration': final_alpha['duration']
        }

class FunimationShowPlaylistIE(FunimationCommonIE):
    IE_NAME = 'Funimation:playlist'
    _VALID_URL = (r'(?P<real_url>https?://(?:www\.)?funimation(?P<ter>\.com|now\.uk)/shows/'+
                 r'(?P<id>[^/?#&]+))/?(?:\?alpha=(?P<alpha>simulcast|uncut))?(?:[?&]lang=(?P<lang>english|japanese))?$')

    def _real_extract(self, url):
        m = re.compile(self._VALID_URL).match(url)
        display_id = m.group('id')
        intended_alpha = m.group('alpha') or 'simulcast'
        intended_language = m.group('lang') or 'english'
        domext = m.group('ter')
        ter = 'US' if (domext == '.com') else 'GB'
        url = m.group('real_url')
        webpage = self._download_webpage(url, display_id)

        title = self._html_search_regex(
            r'(?s)<h2 class="video-title">(.*?)</h2>',
            webpage, 'title')

        show_id = re.findall(r'var showId = (\d+)', webpage)[0]
        try:
            headers = {}
            if self._TOKEN:
                headers['Authorization'] = 'Token %s' % self._TOKEN
            sources = self._download_json(
                'https://prod-api-funimationnow.dadcdigital.com/api/funimation/episodes/?limit=-1&ter=%s&title_id=%s&sort=order&sort_direction=ASC' % (ter, show_id),
                show_id, headers=headers)['items']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error = self._parse_json(e.cause.read(), show_id)['errors'][0]
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error.get('detail') or error.get('title')), expected=True)
            raise

        entries = [
            self.url_result('https://www.funimation%s/shows/%s/%s/%s/?lang=%s'%(
                    domext, ep['item']['titleSlug'], ep['item']['episodeSlug'], intended_alpha, intended_language),
                    'Funimation', ep['item']['episodeName'])
            for ep in sources
        ]

        return {
            '_type': 'playlist',
            'id': display_id,
            'title': title,
            'entries': entries,
        }

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    encode_dict,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class AnimeOnDemandIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?anime-on-demand\.de/anime/(?P<id>\d+)'
    _LOGIN_URL = 'https://www.anime-on-demand.de/users/sign_in'
    _APPLY_HTML5_URL = 'https://www.anime-on-demand.de/html5apply'
    _NETRC_MACHINE = 'animeondemand'
    _TEST = {
        'url': 'https://www.anime-on-demand.de/anime/161',
        'info_dict': {
            'id': '161',
            'title': 'Grimgar, Ashes and Illusions (OmU)',
            'description': 'md5:6681ce3c07c7189d255ac6ab23812d31',
        },
        'playlist_mincount': 4,
    }

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        login_form = self._form_hidden_inputs('new_user', login_page)

        login_form.update({
            'user[login]': username,
            'user[password]': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = compat_urlparse.urljoin(self._LOGIN_URL, post_url)

        request = sanitized_Request(
            post_url, urlencode_postdata(encode_dict(login_form)))
        request.add_header('Referer', self._LOGIN_URL)

        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        if all(p not in response for p in ('>Logout<', 'href="/users/sign_out"')):
            error = self._search_regex(
                r'<p class="alert alert-danger">(.+?)</p>',
                response, 'error', default=None)
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        anime_id = self._match_id(url)

        webpage = self._download_webpage(url, anime_id)

        if 'data-playlist=' not in webpage:
            self._download_webpage(
                self._APPLY_HTML5_URL, anime_id,
                'Activating HTML5 beta', 'Unable to apply HTML5 beta')
            webpage = self._download_webpage(url, anime_id)

        csrf_token = self._html_search_meta(
            'csrf-token', webpage, 'csrf token', fatal=True)

        anime_title = self._html_search_regex(
            r'(?s)<h1[^>]+itemprop="name"[^>]*>(.+?)</h1>',
            webpage, 'anime name')
        anime_description = self._html_search_regex(
            r'(?s)<div[^>]+itemprop="description"[^>]*>(.+?)</div>',
            webpage, 'anime description', default=None)

        entries = []

        for episode_html in re.findall(r'(?s)<h3[^>]+class="episodebox-title".+?>Episodeninhalt<', webpage):
            m = re.search(
                r'class="episodebox-title"[^>]+title="Episode (?P<number>\d+) - (?P<title>.+?)"', episode_html)
            if not m:
                continue

            episode_number = int(m.group('number'))
            episode_title = m.group('title')
            video_id = 'episode-%d' % episode_number

            common_info = {
                'id': video_id,
                'series': anime_title,
                'episode': episode_title,
                'episode_number': episode_number,
            }

            formats = []

            playlist_url = self._search_regex(
                r'data-playlist=(["\'])(?P<url>.+?)\1',
                episode_html, 'data playlist', default=None, group='url')
            if playlist_url:
                request = sanitized_Request(
                    compat_urlparse.urljoin(url, playlist_url),
                    headers={
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRF-Token': csrf_token,
                        'Referer': url,
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                    })

                playlist = self._download_json(
                    request, video_id, 'Downloading playlist JSON', fatal=False)
                if playlist:
                    playlist = playlist['playlist'][0]
                    title = playlist['title']
                    description = playlist.get('description')
                    for source in playlist.get('sources', []):
                        file_ = source.get('file')
                        if file_ and determine_ext(file_) == 'm3u8':
                            formats = self._extract_m3u8_formats(
                                file_, video_id, 'mp4',
                                entry_protocol='m3u8_native', m3u8_id='hls')

            if formats:
                f = common_info.copy()
                f.update({
                    'title': title,
                    'description': description,
                    'formats': formats,
                })
                entries.append(f)

            m = re.search(
                r'data-dialog-header=(["\'])(?P<title>.+?)\1[^>]+href=(["\'])(?P<href>.+?)\3[^>]*>Teaser<',
                episode_html)
            if m:
                f = common_info.copy()
                f.update({
                    'id': '%s-teaser' % f['id'],
                    'title': m.group('title'),
                    'url': compat_urlparse.urljoin(url, m.group('href')),
                })
                entries.append(f)

        return self.playlist_result(entries, anime_id, anime_title, anime_description)

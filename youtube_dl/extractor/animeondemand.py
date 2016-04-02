from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_str,
)
from ..utils import (
    determine_ext,
    extract_attributes,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class AnimeOnDemandIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?anime-on-demand\.de/anime/(?P<id>\d+)'
    _LOGIN_URL = 'https://www.anime-on-demand.de/users/sign_in'
    _APPLY_HTML5_URL = 'https://www.anime-on-demand.de/html5apply'
    _NETRC_MACHINE = 'animeondemand'
    _TESTS = [{
        'url': 'https://www.anime-on-demand.de/anime/161',
        'info_dict': {
            'id': '161',
            'title': 'Grimgar, Ashes and Illusions (OmU)',
            'description': 'md5:6681ce3c07c7189d255ac6ab23812d31',
        },
        'playlist_mincount': 4,
    }, {
        # Film wording is used instead of Episode
        'url': 'https://www.anime-on-demand.de/anime/39',
        'only_matching': True,
    }, {
        # Episodes without titles
        'url': 'https://www.anime-on-demand.de/anime/162',
        'only_matching': True,
    }, {
        # ger/jap, Dub/OmU, account required
        'url': 'https://www.anime-on-demand.de/anime/169',
        'only_matching': True,
    }]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        if '>Our licensing terms allow the distribution of animes only to German-speaking countries of Europe' in login_page:
            self.raise_geo_restricted(
                '%s is only available in German-speaking countries of Europe' % self.IE_NAME)

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
            post_url, urlencode_postdata(login_form))
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

        for num, episode_html in enumerate(re.findall(
                r'(?s)<h3[^>]+class="episodebox-title".+?>Episodeninhalt<', webpage), 1):
            episodebox_title = self._search_regex(
                (r'class="episodebox-title"[^>]+title=(["\'])(?P<title>.+?)\1',
                 r'class="episodebox-title"[^>]+>(?P<title>.+?)<'),
                episode_html, 'episodebox title', default=None, group='title')
            if not episodebox_title:
                continue

            episode_number = int(self._search_regex(
                r'(?:Episode|Film)\s*(\d+)',
                episodebox_title, 'episode number', default=num))
            episode_title = self._search_regex(
                r'(?:Episode|Film)\s*\d+\s*-\s*(.+)',
                episodebox_title, 'episode title', default=None)

            video_id = 'episode-%d' % episode_number

            common_info = {
                'id': video_id,
                'series': anime_title,
                'episode': episode_title,
                'episode_number': episode_number,
            }

            formats = []

            for input_ in re.findall(
                    r'<input[^>]+class=["\'].*?streamstarter_html5[^>]+>', episode_html):
                attributes = extract_attributes(input_)
                playlist_urls = []
                for playlist_key in ('data-playlist', 'data-otherplaylist'):
                    playlist_url = attributes.get(playlist_key)
                    if isinstance(playlist_url, compat_str) and re.match(
                            r'/?[\da-zA-Z]+', playlist_url):
                        playlist_urls.append(attributes[playlist_key])
                if not playlist_urls:
                    continue

                lang = attributes.get('data-lang')
                lang_note = attributes.get('value')

                for playlist_url in playlist_urls:
                    kind = self._search_regex(
                        r'videomaterialurl/\d+/([^/]+)/',
                        playlist_url, 'media kind', default=None)
                    format_id_list = []
                    if lang:
                        format_id_list.append(lang)
                    if kind:
                        format_id_list.append(kind)
                    if not format_id_list:
                        format_id_list.append(compat_str(num))
                    format_id = '-'.join(format_id_list)
                    format_note = ', '.join(filter(None, (kind, lang_note)))
                    request = sanitized_Request(
                        compat_urlparse.urljoin(url, playlist_url),
                        headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRF-Token': csrf_token,
                            'Referer': url,
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                        })
                    playlist = self._download_json(
                        request, video_id, 'Downloading %s playlist JSON' % format_id,
                        fatal=False)
                    if not playlist:
                        continue
                    start_video = playlist.get('startvideo', 0)
                    playlist = playlist.get('playlist')
                    if not playlist or not isinstance(playlist, list):
                        continue
                    playlist = playlist[start_video]
                    title = playlist.get('title')
                    if not title:
                        continue
                    description = playlist.get('description')
                    for source in playlist.get('sources', []):
                        file_ = source.get('file')
                        if not file_:
                            continue
                        ext = determine_ext(file_)
                        format_id_list = [lang, kind]
                        if ext == 'm3u8':
                            format_id_list.append('hls')
                        elif source.get('type') == 'video/dash' or ext == 'mpd':
                            format_id_list.append('dash')
                        format_id = '-'.join(filter(None, format_id_list))
                        if ext == 'm3u8':
                            file_formats = self._extract_m3u8_formats(
                                file_, video_id, 'mp4',
                                entry_protocol='m3u8_native', m3u8_id=format_id, fatal=False)
                        elif source.get('type') == 'video/dash' or ext == 'mpd':
                            continue
                            file_formats = self._extract_mpd_formats(
                                file_, video_id, mpd_id=format_id, fatal=False)
                        else:
                            continue
                        for f in file_formats:
                            f.update({
                                'language': lang,
                                'format_note': format_note,
                            })
                        formats.extend(file_formats)

            if formats:
                self._sort_formats(formats)
                f = common_info.copy()
                f.update({
                    'title': title,
                    'description': description,
                    'formats': formats,
                })
                entries.append(f)

            # Extract teaser only when full episode is not available
            if not formats:
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

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    js_to_json,
    ExtractorError,
    compat_parse_qs,
    compat_urllib_parse_urlparse,
    compat_urllib_parse,
    compat_urllib_request,
    smuggle_url,
    unsmuggle_url
)


class RoosterteethShowIE(InfoExtractor):
    _VALID_URL = r'http://(?P<domain>(?:www\.)?(?:roosterteeth\.com|achievementhunter\.com|fun\.haus))/show/(?P<id>[^/]+)(?:/season)?'
    _TESTS = [{
        'url': 'http://roosterteeth.com/show/screen-play',
        'info_dict': {
            'id': 'screen-play',
            'description': 'A Rooster Teeth podcast focusing on all things Film and TV. Listen to our pop culture geeks chat about TV premieres and finales, blockbuster franchises, indie darlings, casting rumors and spotlight a film to discuss in their weekly "Movie Book Club" segment. So pop some popcorn, grab a good seat and enjoy the show.',
            'title': 'Screen Play',
        },
        'playlist_count': 23
    }, {
        'url': 'http://roosterteeth.com/show/red-vs-blue',
        'info_dict': {
            'id': 'red-vs-blue',
            'description': 'In the distant future, two groups of soldiers battle for control of the least desirable piece of real estate in the known universe - a box canyon in the middle of nowhere.',
            'title': 'Red vs. Blue',
        },

        'playlist_mincount': 380
    }]
    
    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        html = self._download_webpage(url, playlist_id)

        title = self._html_search_regex(r'<div class="show-header">\s*<h1>([^<]+)</h1>\s*</div>', html, 'show title')
        description = self._html_search_regex(r'<section class="show-details">((?:[^<]|<(?!/section>))+)</section>', html, 'show description')

        start_piece = "<div id='tab-content-episodes' class='tab-content'>"
        start = html.find(start_piece)
        if start == -1:
            raise ExtractorError("Can't find the episodes!")

        html = html[start + len(start_piece):].lstrip()
        sections = []
        if html.startswith('<ul class='):
            # This show doesn't have seasons AKA sections.
            end = html.find('</ul>')
            if end == -1:
                raise ExtractorError("Can't find the end of the episode list!")

            sections = [(None, html[:end])]
        else:
            # We have to extract the sections.
            end = html.find('</article></section></section>')
            if end == -1:
                raise ExtractorError("Can't find the end of the section list!")

            html = html[:end]
            HEADER_RE = re.compile(r"<h3 class='title' id='header-[^']+'>([^<]+)</h3>")

            # Process sections / seasons
            for section in html.split('</section>'):
                sec_title = self._html_search_regex(HEADER_RE, section, 'season title')
                start = section.find("<ul class='episode-blocks'>")
                end = section.find("</ul>", start)

                if start < 0 or end < 0:
                    raise ExtractorError("Couldn't parse season %s! (%s)" % (sec_title, playlist_id))

                sections.append((sec_title, section[start:end]))

        results = []
        EP_RE = re.compile(r'<a href="(?P<url>[^"]+)">(?:[^<]|<(?!p class="name"))+<p class="name">(?P<title>[^<]+)</p>\s*</a>')

        for sec_title, part in reversed(sections):
            episodes = part.split('</li>')
            for ep_part in episodes:
                if ep_part.strip() == '':
                    continue

                ep = EP_RE.search(ep_part)
                if not ep:
                    raise ExtractorError("Failed to parse an episode of season %s! (%s, %s)" % (sec_title or '0', playlist_id, ep_part))

                url = clean_html(ep.group('url'))
                res = self.url_result(url, 'Roosterteeth')
                res['title'] = clean_html(ep.group('title'))

                if sec_title:
                    res['url'] = smuggle_url(res['url'], {'season': sec_title})
                    res['title'] = '%s: %s' % (sec_title, res['title'])

                results.append(res)

        if len(sections) == 1 and sections[0][0] is None:
            # If the page didn't contain sections, then the episodes are in reverse order.
            results = list(reversed(results))

        return self.playlist_result(results, playlist_id, title, description)


class RoosterteethIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<domain>(?:www\.)?(?:roosterteeth\.com|achievementhunter\.com|fun\.haus))/episode/(?P<id>[^/]+)'
    _TESTS = [
        {
            'url': 'http://achievementhunter.com/episode/rage-quit-season-1-episode-199',
            'md5': '828fe30ccdddf5d85e444e33686d531a',
            'info_dict': {
                'id': 'rage-quit-season-1-episode-199',
                'ext': 'mp4',
                'title': 'Rage Quit - No Time to Explain',
                'description': 'There\'s no time to explain this video.',
                'thumbnail': r're:^https?://.*\.jpeg$',
                'protocol': 'm3u8_native',
                'url': r're:^https?://[a-zA-Z0-9.]+\.taucdn\.net/.*\.m3u8$',
            }
        },
        {
            'url': 'http://roosterteeth.com/episode/red-vs-blue-season-1-episode-1',
            'md5': '80277833f3ed946b553d13cf8e27443d',
            'info_dict': {
                'id': 'red-vs-blue-season-1-episode-1',
                'ext': 'mp4',
                
                'title': 'Episode 1',
                'thumbnail': r're:^https://i\.ytimg\.com/vi/[0-9a-zA-Z]+/maxresdefault\.jpg$',
                'url': r're:^https://[0-9a-z-]+\.googlevideo\.com/videoplayback',

                'upload_date': '20150306',
                'uploader_id': 'UCII0hP2Ycmhh5j8lS4cexBQ',
                'uploader': 'Red vs. Blue',
                'description': 'The first episode of Red vs. Blue introduces the main characters, and poses the all-important question, why are we here?'
            }
        }
    ]
    _NETRC_MACHINE = 'roosterteeth'
    _authed = None
    _sponsor = None

    def _real_initialize(self):
        self._authed = {}

    def _real_extract(self, url):
        url, data = unsmuggle_url(url)
        video_id = self._match_id(url)
        html = self._download_webpage(url, video_id)

        if html.find('Unfortunately, this is sponsor-only.') > -1:
            domain = compat_urllib_parse_urlparse(url).netloc
            release = re.search(r'<p>[^<]+ Releases ([0-9]+ [a-zA-Z]+) from now</p>', html)
            if release:
                release = ' The video will be public in %s.' % release.group(1)
            else:
                release = ''

            if not self._login(domain):
                raise ExtractorError("This video is sponsor-only. You didn't provide your credentials or the login failed.%s" % release, expected=True)

            # Try again.
            html = self._download_webpage(url, video_id)
            if html.find('Unfortunately, this is sponsor-only.') > -1:
                if not self._is_sponsor(domain):
                    raise ExtractorError('This video is sponsor-only but you are not a sponsor.%s' % release, expected=True)
                else:
                    raise ExtractorError('This is a sponsor-only video and although I tried to login, it did not work.')

        p = re.search(r'<script src="https?://(?:www\.)?(?:roosterteeth\.com|achievementhunter\.com|fun\.haus)/scripts/lib/(?P<player>jwplayer|youtube)\.(?:min\.)?js"></script>\s*<script>\s*(?P<script>[^<]+)\s*</script>', html)
        if not p:
            raise ExtractorError("Can't parse the video metadata! (%s)" % video_id)

        player = p.group('player')
        if player == 'jwplayer':
            video_image = self._search_regex(r"var videoImage = '([^']+)';", p.group('script'), 'video image')
            if video_image.startswith('//'):
                video_image = 'http:' + video_image

            manifest = self._search_regex(r"RT\.jwplayer\.player\([^\{]+\{\s*file: '([^']+)',", p.group('script'), 'manifest')

            res = {
                'id': video_id,
                'formats': self._extract_m3u8_formats(manifest, video_id, ext='mp4'),
                'thumbnail': video_image
            }
        elif player == 'youtube':
            info = self._html_search_regex(r'RT\.(?:youtube|jwplayer)\.player\((\{(?:[^}]|\}(?!\);))+\})\);', p.group('script'), 'video metadata')
            meta = self._parse_json(js_to_json(info), video_id)

            if 'youtubeKey' not in meta:
                raise ExtractorError('Invalid metadata for youtube video!')

            res = {
                '_type': 'url_transparent',
                'url': 'https://youtube.com/watch?v=' + meta['youtubeKey'],
                'id': video_id
            }
        else:
            raise ExtractorError('Unknown player type %s!' % player)

        desc = self._og_search_description(html)
        if desc:
            res['description'] = desc.strip()

        res['raw_title'] = self._html_search_regex(r'<title>([^<]+)</title>', html, 'video title')
        if data and 'season' in data:
            res['title'] = '%s: %s' % (data['season'], res['raw_title'])
            res['season'] = data['season']
        else:
            res['title'] = res['raw_title']

        return res

    def _login(self, domain='roosterteeth.com'):
        """
        Attempt to log in to RoosterTeeth (or Achievement Hunter).
        NOTE: RT is planning to implement SSO which will probably change how this works.
        """

        if domain in self._authed:
            return self._authed[domain]

        (username, password) = self._get_login_info()

        # No authentication to be performed
        if username is None:
            return False

        LOGIN_URL = 'http://%s/login' % domain
        login_page, hdl = self._download_webpage_handle(
            LOGIN_URL, None,
            note='Downloading login page',
            errnote='unable to fetch login page', fatal=False)

        if login_page is False:
            return False

        if hdl.geturl() != LOGIN_URL:
            # We were redirected which means that we're already logged in.
            self._authed[domain] = True
            return True
        
        token = self._search_regex(r'(?s)<input.+?name="_token".+?value="(.+?)"',
                                   login_page, 'Login token')

        # Log in
        login_form_strs = {
            '_token': token,
            'username': username,
            'password': password
        }

        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')

        req = compat_urllib_request.Request(LOGIN_URL, login_data, {'Content-Type': 'application/x-www-form-urlencoded'})
        login_results = self._download_webpage(
            req, None,
            note='Logging in', errnote='unable to log in', fatal=False)
        
        if login_results is False:
            return False

        if login_results.find('Error in exception handler.') > -1 or login_results.find('Authentication failed. Please check and try again, or reset your password') > -1:
            self.report_warning('unable to log in: bad username or password')
            self._authed[domain] = False
            return False

        self._authed[domain] = True
        return True

    def _is_sponsor(self, domain='roosterteeth.com'):
        if self._sponsor is None:
            username, _ = self._get_login_info()
            profile_page = 'http://%s/user/%s' % (domain, compat_urllib_parse.quote(username))
            html = self._download_webpage(
                profile_page, None,
                note='Checking user profile',
                errnote='unable to access user profile', fatal=False)

            if not html:
                return False

            user_info = self._search_regex(
                r'<div class="sidebar-profile-header">\s*<p[^>]+>\s*<a href="%s">[^<]+</a>\s*<span>((?:[^<]|<(?!/span>))+)</span>' % (profile_page),
                html, 'user status', fatal=False)

            if not user_info:
                return False

            self._sponsor = '<i class="icon ion-star"></i>' in user_info

        return self._sponsor

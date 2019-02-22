# coding: utf-8
from __future__ import unicode_literals

import functools
import itertools
import math
import operator
import re

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
    compat_urllib_request,
)
from .openload import PhantomJSwrapper
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    remove_quotes,
    str_to_int,
    url_or_none,
)


class PornHubBaseIE(InfoExtractor):
    def _download_webpage_handle(self, *args, **kwargs):
        def dl(*args, **kwargs):
            return super(PornHubBaseIE, self)._download_webpage_handle(*args, **kwargs)

        def rnkey_is_required(webpage):
            """Check if a RNKEY cookie is required to access the real page."""
            return any(re.search(p, webpage)
                       for p in (r'<body\b[^>]+\bonload=["\']go\(\)',
                                 r'document\.cookie\s*=\s*["\']RNKEY=',
                                 r'document\.location\.reload\(true\)'))

        re_opts = re.ASCII | re.DOTALL | re.VERBOSE

        def product(nums):
            return functools.reduce(operator.mul, nums, 1)

        def compose(*funcs):
            """Compose sequence of unary functions `funcs`."""
            def compose2(g, f):
                return lambda x: g(f(x))

            return functools.reduce(compose2, funcs, lambda x: x)

        def fermat_factor(n):
            """
            Use Fermat's factorization method to factorize `n` into `c``d`
            where `n` >= 1 and `c` <= `d`.
            The factorization is proper whenever `n` is composite.
            """
            if n == 2:
                return 1, 2
            elif n % 2 == 0:
                return 2, n // 2
            else:
                for a in range(math.ceil(math.sqrt(n)), n + 1):
                    b = math.sqrt(a ** 2 - n)
                    if b.is_integer():
                        return a - int(b), a + int(b)

        def find_func(name, string):
            """Extract function `name` from `string`."""
            match, = re.findall(r'function \s+ %s \s* \( \s* \) \s* \{ (.+) \}'
                                % re.escape(name),
                                string,
                                re_opts)
            return match

        def strip_comments(string):
            """Strip away /* ... */ and // ... \n comments from `string`."""
            return re.sub(r'/\* (?: \*+ [^*/] | [^*])* \** \*/ | // [^\n]* \n',
                          '\n',
                          string,
                          flags=re_opts)

        def find_init_val(name, string):
            """
            Extract initial value for integer variable `name`
            from `string`.
            """
            match, = re.findall(r'var \s+ %s \s* = \s* (\d+)'
                                % re.escape(name),
                                string,
                                re_opts)
            return int(match)

        def plus_minus_product(sign, *nums):
            """
            Create a unary function which takes an integer and
            adds / substracts product of `nums` to it according to `sign`.
            """
            n = product(map(int, nums))
            if sign == '+':
                return lambda k: k + n
            elif sign == '-':
                return lambda k: k - n

        def parse_if_else_actions(s, string):
            """
            Create a list of unary functions which takes an integer and
            adds / substracts to it according to bits of `s`
            and actions in `string`.
            """
            def process_match(bit, sign_1, n_11, n_12, sign_2, n_21, n_22):
                if (s >> int(bit)) & 1 == 1:
                    return plus_minus_product(sign_1, n_11, n_12)
                else:
                    return plus_minus_product(sign_2, n_21, n_22)

            matches = re.findall(r'''
            if [^>]+ s \s* >> \s* (\d+) [^=]+
            p \s* ([-+])= \s* (\d+) \s* \* \s* (\d+) [^=]+
            else \s+
            p \s* ([-+])= \s* (\d+) \s* \* \s* (\d+)''',
                                 string,
                                 re_opts)
            return [process_match(*match) for match in matches]

        def parse_last_action(string):
            """
            Create a unary function which takes an integer and
            adds / substracts to it according to the last action in `string`.
            """
            match, = re.findall(r'.+ p \s* ([-+])= \s* (\d+)', string, re_opts)
            return plus_minus_product(*match)

        def find_magic_number(string):
            """Extract colon enclosed magic number from `string`."""
            match, = re.findall(r':(\d+):1', string, re_opts)
            return int(match)

        def generate_rnkey_cookie(string):
            """Extract relevant data from `string` to generate RNKEY cookie."""
            go = strip_comments(find_func('go', string))

            p = find_init_val('p', go)
            s = find_init_val('s', go)

            if_else_actions = parse_if_else_actions(s, go)
            last_action = parse_last_action(go)
            # actions are commutative, we can compose in whatever order we wish
            composite_action = compose(last_action, *if_else_actions)
            smaller_factor, larger_factor = fermat_factor(composite_action(p))

            magic_num = find_magic_number(go)

            return {'domain': 'pornhub.com',
                    'name': 'RNKEY',
                    'value': '%s*%s:%s:%s:1'
                    % (smaller_factor, larger_factor, s, magic_num)}

        webpage, urlh = dl(*args, **kwargs)

        if rnkey_is_required(webpage):
            try:
                # try to generate a RNKEY cookie and re-download the page
                self._set_cookie(**generate_rnkey_cookie(webpage))
                webpage, urlh = dl(*args, **kwargs)
                assert(not rnkey_is_required(webpage))
            except Exception as e:
                self.report_warning('Unable to generate RNKEY cookie: %s' % e)
                # only invoke phantumjs as a last resort
                url_or_request = args[0]
                url = (url_or_request.get_full_url()
                       if isinstance(url_or_request,
                                     compat_urllib_request.Request)
                       else url_or_request)
                phantom = PhantomJSwrapper(self, required_version='2.0')
                phantom.get(url, html=webpage)
                webpage, urlh = dl(*args, **kwargs)

        return webpage, urlh


class PornHubIE(PornHubBaseIE):
    IE_DESC = 'PornHub and Thumbzilla'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?(?P<host>pornhub\.(?:com|net))/(?:(?:view_video\.php|video/show)\?viewkey=|embed/)|
                            (?:www\.)?thumbzilla\.com/video/
                        )
                        (?P<id>[\da-z]+)
                    '''
    _TESTS = [{
        'url': 'http://www.pornhub.com/view_video.php?viewkey=648719015',
        'md5': '1e19b41231a02eba417839222ac9d58e',
        'info_dict': {
            'id': '648719015',
            'ext': 'mp4',
            'title': 'Seductive Indian beauty strips down and fingers her pink pussy',
            'uploader': 'Babes',
            'upload_date': '20130628',
            'duration': 361,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 18,
            'tags': list,
            'categories': list,
        },
    }, {
        # non-ASCII title
        'url': 'http://www.pornhub.com/view_video.php?viewkey=1331683002',
        'info_dict': {
            'id': '1331683002',
            'ext': 'mp4',
            'title': '重庆婷婷女王足交',
            'uploader': 'Unknown',
            'upload_date': '20150213',
            'duration': 1753,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 18,
            'tags': list,
            'categories': list,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # subtitles
        'url': 'https://www.pornhub.com/view_video.php?viewkey=ph5af5fef7c2aa7',
        'info_dict': {
            'id': 'ph5af5fef7c2aa7',
            'ext': 'mp4',
            'title': 'BFFS - Cute Teen Girls Share Cock On the Floor',
            'uploader': 'BFFs',
            'duration': 622,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 18,
            'tags': list,
            'categories': list,
            'subtitles': {
                'en': [{
                    "ext": 'srt'
                }]
            },
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.pornhub.com/view_video.php?viewkey=ph557bbb6676d2d',
        'only_matching': True,
    }, {
        # removed at the request of cam4.com
        'url': 'http://fr.pornhub.com/view_video.php?viewkey=ph55ca2f9760862',
        'only_matching': True,
    }, {
        # removed at the request of the copyright owner
        'url': 'http://www.pornhub.com/view_video.php?viewkey=788152859',
        'only_matching': True,
    }, {
        # removed by uploader
        'url': 'http://www.pornhub.com/view_video.php?viewkey=ph572716d15a111',
        'only_matching': True,
    }, {
        # private video
        'url': 'http://www.pornhub.com/view_video.php?viewkey=ph56fd731fce6b7',
        'only_matching': True,
    }, {
        'url': 'https://www.thumbzilla.com/video/ph56c6114abd99a/horny-girlfriend-sex',
        'only_matching': True,
    }, {
        'url': 'http://www.pornhub.com/video/show?viewkey=648719015',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.net/view_video.php?viewkey=203640933',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//(?:www\.)?pornhub\.(?:com|net)/embed/[\da-z]+)',
            webpage)

    def _extract_count(self, pattern, webpage, name):
        return str_to_int(self._search_regex(
            pattern, webpage, '%s count' % name, fatal=False))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host') or 'pornhub.com'
        video_id = mobj.group('id')

        self._set_cookie(host, 'age_verified', '1')

        def dl_webpage(platform):
            self._set_cookie(host, 'platform', platform)
            return self._download_webpage(
                'http://www.%s/view_video.php?viewkey=%s' % (host, video_id),
                video_id, 'Downloading %s webpage' % platform)

        webpage = dl_webpage('pc')

        error_msg = self._html_search_regex(
            r'(?s)<div[^>]+class=(["\'])(?:(?!\1).)*\b(?:removed|userMessageSection)\b(?:(?!\1).)*\1[^>]*>(?P<error>.+?)</div>',
            webpage, 'error message', default=None, group='error')
        if error_msg:
            error_msg = re.sub(r'\s+', ' ', error_msg)
            raise ExtractorError(
                'PornHub said: %s' % error_msg,
                expected=True, video_id=video_id)

        # video_title from flashvars contains whitespace instead of non-ASCII (see
        # http://www.pornhub.com/view_video.php?viewkey=1331683002), not relying
        # on that anymore.
        title = self._html_search_meta(
            'twitter:title', webpage, default=None) or self._search_regex(
            (r'<h1[^>]+class=["\']title["\'][^>]*>(?P<title>[^<]+)',
             r'<div[^>]+data-video-title=(["\'])(?P<title>.+?)\1',
             r'shareTitle\s*=\s*(["\'])(?P<title>.+?)\1'),
            webpage, 'title', group='title')

        video_urls = []
        video_urls_set = set()
        subtitles = {}

        flashvars = self._parse_json(
            self._search_regex(
                r'var\s+flashvars_\d+\s*=\s*({.+?});', webpage, 'flashvars', default='{}'),
            video_id)
        if flashvars:
            subtitle_url = url_or_none(flashvars.get('closedCaptionsFile'))
            if subtitle_url:
                subtitles.setdefault('en', []).append({
                    'url': subtitle_url,
                    'ext': 'srt',
                })
            thumbnail = flashvars.get('image_url')
            duration = int_or_none(flashvars.get('video_duration'))
            media_definitions = flashvars.get('mediaDefinitions')
            if isinstance(media_definitions, list):
                for definition in media_definitions:
                    if not isinstance(definition, dict):
                        continue
                    video_url = definition.get('videoUrl')
                    if not video_url or not isinstance(video_url, compat_str):
                        continue
                    if video_url in video_urls_set:
                        continue
                    video_urls_set.add(video_url)
                    video_urls.append(
                        (video_url, int_or_none(definition.get('quality'))))
        else:
            thumbnail, duration = [None] * 2

        if not video_urls:
            tv_webpage = dl_webpage('tv')

            assignments = self._search_regex(
                r'(var.+?mediastring.+?)</script>', tv_webpage,
                'encoded url').split(';')

            js_vars = {}

            def parse_js_value(inp):
                inp = re.sub(r'/\*(?:(?!\*/).)*?\*/', '', inp)
                if '+' in inp:
                    inps = inp.split('+')
                    return functools.reduce(
                        operator.concat, map(parse_js_value, inps))
                inp = inp.strip()
                if inp in js_vars:
                    return js_vars[inp]
                return remove_quotes(inp)

            for assn in assignments:
                assn = assn.strip()
                if not assn:
                    continue
                assn = re.sub(r'var\s+', '', assn)
                vname, value = assn.split('=', 1)
                js_vars[vname] = parse_js_value(value)

            video_url = js_vars['mediastring']
            if video_url not in video_urls_set:
                video_urls.append((video_url, None))
                video_urls_set.add(video_url)

        for mobj in re.finditer(
                r'<a[^>]+\bclass=["\']downloadBtn\b[^>]+\bhref=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage):
            video_url = mobj.group('url')
            if video_url not in video_urls_set:
                video_urls.append((video_url, None))
                video_urls_set.add(video_url)

        upload_date = None
        formats = []
        for video_url, height in video_urls:
            if not upload_date:
                upload_date = self._search_regex(
                    r'/(\d{6}/\d{2})/', video_url, 'upload data', default=None)
                if upload_date:
                    upload_date = upload_date.replace('/', '')
            tbr = None
            mobj = re.search(r'(?P<height>\d+)[pP]?_(?P<tbr>\d+)[kK]', video_url)
            if mobj:
                if not height:
                    height = int(mobj.group('height'))
                tbr = int(mobj.group('tbr'))
            formats.append({
                'url': video_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
                'tbr': tbr,
            })
        self._sort_formats(formats)

        video_uploader = self._html_search_regex(
            r'(?s)From:&nbsp;.+?<(?:a\b[^>]+\bhref=["\']/(?:(?:user|channel)s|model|pornstar)/|span\b[^>]+\bclass=["\']username)[^>]+>(.+?)<',
            webpage, 'uploader', fatal=False)

        view_count = self._extract_count(
            r'<span class="count">([\d,\.]+)</span> views', webpage, 'view')
        like_count = self._extract_count(
            r'<span class="votesUp">([\d,\.]+)</span>', webpage, 'like')
        dislike_count = self._extract_count(
            r'<span class="votesDown">([\d,\.]+)</span>', webpage, 'dislike')
        comment_count = self._extract_count(
            r'All Comments\s*<span>\(([\d,.]+)\)', webpage, 'comment')

        def extract_list(meta_key):
            div = self._search_regex(
                r'(?s)<div[^>]+\bclass=["\'].*?\b%sWrapper[^>]*>(.+?)</div>'
                % meta_key, webpage, meta_key, default=None)
            if div:
                return re.findall(r'<a[^>]+\bhref=[^>]+>([^<]+)', div)

        return {
            'id': video_id,
            'uploader': video_uploader,
            'upload_date': upload_date,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
            'tags': extract_list('tags'),
            'categories': extract_list('categories'),
            'subtitles': subtitles,
        }


class PornHubPlaylistBaseIE(PornHubBaseIE):
    def _extract_entries(self, webpage, host):
        # Only process container div with main playlist content skipping
        # drop-down menu that uses similar pattern for videos (see
        # https://github.com/rg3/youtube-dl/issues/11594).
        container = self._search_regex(
            r'(?s)(<div[^>]+class=["\']container.+)', webpage,
            'container', default=webpage)

        return [
            self.url_result(
                'http://www.%s/%s' % (host, video_url),
                PornHubIE.ie_key(), video_title=title)
            for video_url, title in orderedSet(re.findall(
                r'href="/?(view_video\.php\?.*\bviewkey=[\da-z]+[^"]*)"[^>]*\s+title="([^"]+)"',
                container))
        ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)

        entries = self._extract_entries(webpage, host)

        playlist = self._parse_json(
            self._search_regex(
                r'(?:playlistObject|PLAYLIST_VIEW)\s*=\s*({.+?});', webpage,
                'playlist', default='{}'),
            playlist_id, fatal=False)
        title = playlist.get('title') or self._search_regex(
            r'>Videos\s+in\s+(.+?)\s+[Pp]laylist<', webpage, 'title', fatal=False)

        return self.playlist_result(
            entries, playlist_id, title, playlist.get('description'))


class PornHubPlaylistIE(PornHubPlaylistBaseIE):
    _VALID_URL = r'https?://(?:[^/]+\.)?(?P<host>pornhub\.(?:com|net))/playlist/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.pornhub.com/playlist/4667351',
        'info_dict': {
            'id': '4667351',
            'title': 'Nataly Hot',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://de.pornhub.com/playlist/4667351',
        'only_matching': True,
    }]


class PornHubUserVideosIE(PornHubPlaylistBaseIE):
    _VALID_URL = r'https?://(?:[^/]+\.)?(?P<host>pornhub\.(?:com|net))/(?:(?:user|channel)s|model|pornstar)/(?P<id>[^/]+)/videos'
    _TESTS = [{
        'url': 'http://www.pornhub.com/users/zoe_ph/videos/public',
        'info_dict': {
            'id': 'zoe_ph',
        },
        'playlist_mincount': 171,
    }, {
        'url': 'http://www.pornhub.com/users/rushandlia/videos',
        'only_matching': True,
    }, {
        # default sorting as Top Rated Videos
        'url': 'https://www.pornhub.com/channels/povd/videos',
        'info_dict': {
            'id': 'povd',
        },
        'playlist_mincount': 293,
    }, {
        # Top Rated Videos
        'url': 'https://www.pornhub.com/channels/povd/videos?o=ra',
        'only_matching': True,
    }, {
        # Most Recent Videos
        'url': 'https://www.pornhub.com/channels/povd/videos?o=da',
        'only_matching': True,
    }, {
        # Most Viewed Videos
        'url': 'https://www.pornhub.com/channels/povd/videos?o=vi',
        'only_matching': True,
    }, {
        'url': 'http://www.pornhub.com/users/zoe_ph/videos/public',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/model/jayndrea/videos/upload',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/pornstar/jenny-blighe/videos/upload',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        user_id = mobj.group('id')

        entries = []
        for page_num in itertools.count(1):
            try:
                webpage = self._download_webpage(
                    url, user_id, 'Downloading page %d' % page_num,
                    query={'page': page_num})
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                    break
                raise
            page_entries = self._extract_entries(webpage, host)
            if not page_entries:
                break
            entries.extend(page_entries)

        return self.playlist_result(entries, user_id)

# coding: utf-8
from __future__ import unicode_literals

import functools
import itertools
import operator
import re

from .common import InfoExtractor

from ..compat import (
    compat_HTTPError,
)
from .openload import PhantomJSwrapper
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    ExtractorError,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    merge_dicts,
    parse_count,
    remove_quotes,
    remove_start,
    T,
    traverse_obj,
    update_url_query,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class PornHubBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'pornhub'
    _PORNHUB_HOST_RE = r'(?:(?P<host>pornhub(?:premium)?\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\.onion)'

    def _download_webpage_handle(self, *args, **kwargs):
        def dl(*args, **kwargs):
            return super(PornHubBaseIE, self)._download_webpage_handle(*args, **kwargs)

        ret = dl(*args, **kwargs)

        if not ret:
            return ret

        webpage, urlh = ret

        if any(re.search(p, webpage) for p in (
                r'<body\b[^>]+\bonload=["\']go\(\)',
                r'document\.cookie\s*=\s*["\']RNKEY=',
                r'document\.location\.reload\(true\)')):
            url = urlh.geturl()
            phantom = PhantomJSwrapper(self, required_version='2.0')
            phantom.get(url, html=webpage)
            webpage, urlh = dl(*args, **kwargs)

        return webpage, urlh

    def _real_initialize(self):
        self._logged_in = False

    def _set_age_cookies(self, host):
        self._set_cookie(host, 'age_verified', '1')
        self._set_cookie(host, 'accessAgeDisclaimerPH', '1')
        self._set_cookie(host, 'accessAgeDisclaimerUK', '1')
        self._set_cookie(host, 'accessPH', '1')

    def _login(self, host):
        if self._logged_in:
            return

        site = host.split('.', 1)[0]

        # Both sites pornhub and pornhubpremium have separate accounts
        # so there should be an option to provide credentials for both.
        # At the same time some videos are available under the same video id
        # on both sites so that we have to identify them as the same video.
        # For that purpose we have to keep both in the same extractor
        # but under different netrc machines.
        username, password = self._get_login_info(netrc_machine=site)
        if username is None:
            return

        login_url = 'https://www.%s/%slogin' % (host, 'premium/' if 'premium' in host else '')
        login_page = self._download_webpage(
            login_url, None, 'Downloading %s login page' % site)

        def is_logged(webpage):
            return bool(
                get_element_by_id('profileMenuDropdown', webpage)
                or get_element_by_class('ph-icon-logout', webpage))

        if is_logged(login_page):
            self._logged_in = True
            return

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'email': username,
            'password': password,
        })

        response = self._download_json(
            'https://www.%s/front/authenticate' % host, 'login',
            'Logging in to %s' % site,
            data=urlencode_postdata(login_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': login_url,
                'X-Requested-With': 'XMLHttpRequest',
            })

        if response.get('success') == '1':
            self._logged_in = True
            return

        message = response.get('message')
        if message is not None:
            raise ExtractorError(
                'Unable to login: %s' % message, expected=True)

        raise ExtractorError('Unable to log in')


class PornHubIE(PornHubBaseIE):
    IE_DESC = 'PornHub'  # Thumbzilla -> Redtube.com, Modelhub -> uviu.com
    _PORNHUB_PATH_RE = r'/(?:(?:view_video\.php%s)\?(?:.+&)?viewkey=%s)(?P<id>[\da-z]+)'
    _VALID_URL = r'https?://(?:[^/]+\.)?%s%s' % (
        PornHubBaseIE._PORNHUB_HOST_RE, _PORNHUB_PATH_RE % ('|video/show', '|embed/'))
    _PORNHUB_PATH_RE = _PORNHUB_PATH_RE % ('', '')
    _EMBED_REGEX = [r'<iframe\s[^>]*?src=["\'](?P<url>(?:https?:)?//(?:www\.)?pornhub(?:premium)?\.(?:com|net|org)/embed/[\da-z]+)']
    _TESTS = [{
        'url': 'http://www.pornhub.com/view_video.php?viewkey=648719015',
        'md5': 'a6391306d050e4547f62b3f485dd9ba9',
        'info_dict': {
            'id': '648719015',
            'ext': 'mp4',
            'title': 'Seductive Indian beauty strips down and fingers her pink pussy',
            'uploader': 'Babes',
            'uploader_id': '/users/babes-com',
            'upload_date': '20130628',
            'timestamp': 1372447216,
            'duration': 361,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 18,
            'tags': list,
            'categories': list,
            'cast': list,
        },
        'params': {
            'format': '[format_id!^=hls]',
        },
    }, {
        # non-ASCII title
        'url': 'http://www.pornhub.com/view_video.php?viewkey=1331683002',
        'info_dict': {
            'id': '1331683002',
            'ext': 'mp4',
            'title': '重庆婷婷女王足交',
            'upload_date': '20150213',
            'timestamp': 1423804862,
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
        'skip': 'Video has been flagged for verification in accordance with our trust and safety policy',
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
                    'ext': 'srt',
                }],
            },
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'This video has been disabled',
    }, {
        'url': 'http://www.pornhub.com/view_video.php?viewkey=ph601dc30bae19a',
        'info_dict': {
            'id': 'ph601dc30bae19a',
            'ext': 'mp4',
            'timestamp': 1612564932,
            'age_limit': 18,
            'uploader': 'Projekt Melody',
            'uploader_id': 'projekt-melody',
            'upload_date': '20210205',
            'title': '"Welcome to My Pussy Mansion" - CB Stream (02/03/21)',
            'thumbnail': r're:https?://.+',
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
        'url': 'http://www.pornhub.com/video/show?viewkey=648719015',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.net/view_video.php?viewkey=203640933',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.org/view_video.php?viewkey=203640933',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhubpremium.com/view_video.php?viewkey=ph5e4acdae54a82',
        'only_matching': True,
    }, {
        # Some videos are available with the same id on both premium
        # and non-premium sites (e.g. this and the following test)
        'url': 'https://www.pornhub.com/view_video.php?viewkey=ph5f75b0f4b18e3',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhubpremium.com/view_video.php?viewkey=ph5f75b0f4b18e3',
        'only_matching': True,
    }, {
        # geo restricted
        'url': 'https://www.pornhub.com/view_video.php?viewkey=ph5a9813bfa7156',
        'only_matching': True,
    }, {
        'url': 'http://pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd.onion/view_video.php?viewkey=ph5a9813bfa7156',
        'only_matching': True,
    }]

    @classmethod
    def _extract_urls(cls, webpage):
        def yield_urls():
            for p in cls._EMBED_REGEX:
                for from_ in re.finditer(p, webpage):
                    yield from_.group('url')

        return list(yield_urls())

    def _extract_count(self, pattern, webpage, name):
        return parse_count(self._search_regex(
            pattern, webpage, '%s count' % name, fatal=False))

    def _real_extract(self, url):
        for _ in range(2):
            mobj = self._match_valid_url(url)
            video_id = mobj.group('id') if mobj else self._generic_id(url)
            _, urlh = self._download_webpage_handle(url, video_id)
            if url == urlh.geturl():
                break
            url = urlh.geturl()

        host = mobj.group('host') or 'pornhub.com'

        self._login(host)
        self._set_age_cookies(host)

        def dl_webpage(platform):
            self._set_cookie(host, 'platform', platform)
            return self._download_webpage(
                'https://www.%s/view_video.php?viewkey=%s' % (host, video_id),
                video_id, 'Downloading %s webpage' % platform)

        webpage = dl_webpage('pc')

        error_msg = self._html_search_regex(
            (r'(?s)<div[^>]+class=("|\')(?:(?!\1).)*\b(?:removed|userMessageSection)\b(?:(?!\1).)*\1[^>]*>(?P<error>.+?)</div>',
             r'(?s)<section[^>]+class=["\']noVideo["\'][^>]*>(?P<error>.+?)</section>'),
            webpage, 'error message', default=None, group='error')
        if error_msg:
            error_msg = re.sub(r'\s+', ' ', error_msg)
            raise ExtractorError(
                'PornHub said: %s' % error_msg,
                expected=True, video_id=video_id)

        if bool(get_element_by_class('geoBlocked', webpage)
                or self._search_regex(
                    r'>\s*This content is (unavailable) in your country', webpage, 'geo-restriction', default=False)):
            self.raise_geo_restricted()

        # video_title from flashvars contains whitespace instead of non-ASCII (see
        # http://www.pornhub.com/view_video.php?viewkey=1331683002), not relying
        # on that anymore.
        title = self._html_search_meta(
            'twitter:title', webpage, default=None) or self._html_search_regex(
            (r'(?s)<h1[^>]+class=["\']title["\'][^>]*>(?P<title>.+?)</h1>',
             r'<div[^>]+data-video-title=(["\'])(?P<title>(?:(?!\1).)+)\1',
             r'shareTitle["\']\s*[=:]\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', group='title')

        video_urls = []
        video_urls_set = set()
        subtitles = {}

        def add_video_url(video_url, quality=None):
            v_url = url_or_none(video_url)
            if not v_url:
                return
            if v_url in video_urls_set:
                return
            video_urls.append((v_url, quality))
            video_urls_set.add(v_url)

        flashvars = self._search_json(r'var\s+flashvars_\d+\s*=', webpage, 'flashvars', video_id)
        flashvars = traverse_obj(flashvars, {
            'closedCaptionsFile': ('closedCaptionsFile', T(url_or_none)),
            'image_url': ('image_url', T(url_or_none)),
            'video_duration': ('video_duration', T(int_or_none)),
            'mediaDefinitions': ('mediaDefinitions', lambda _, v: v['videoUrl']),
        }) or {}
        subtitle_url = flashvars.get('closedCaptionsFile')
        if subtitle_url:
            subtitles.setdefault('en', []).append({
                'url': subtitle_url,
                'ext': 'srt',
            })
        thumbnail = flashvars.get('image_url')
        duration = flashvars.get('video_duration')
        for definition in flashvars.get('mediaDefinitions') or []:
            add_video_url(definition['videoUrl'], int_or_none(definition.get('quality')))

        def extract_js_vars(webpage, pattern, default=None):
            assignments = self._search_regex(
                pattern, webpage, 'encoded url', default=default)
            if not assignments:
                return {}

            assignments = assignments.split(';')

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
            return js_vars

        def parse_quality_items(quality_items):
            q_items = self._parse_json(quality_items, video_id, fatal=False)
            for v_url in traverse_obj(q_items, (Ellipsis, 'url')):
                add_video_url(v_url)

        if not video_urls:
            FORMAT_PREFIXES = ('media', 'quality', 'qualityItems')
            js_vars = extract_js_vars(
                webpage, r'(var\s+(?:%s)_.+)' % '|'.join(FORMAT_PREFIXES))
            for key, format_url in js_vars.items():
                if key.startswith(FORMAT_PREFIXES[-1]):
                    parse_quality_items(format_url)
                elif any(key.startswith(p) for p in FORMAT_PREFIXES[:2]):
                    add_video_url(format_url)
            if not video_urls and get_element_by_id('lockedPlayer', webpage):
                raise ExtractorError(
                    'Video %s is locked' % video_id, expected=True)

        if not video_urls:
            js_vars = extract_js_vars(
                dl_webpage('tv'), r'(var.+?mediastring.+?)</script>')
            add_video_url(traverse_obj(js_vars, 'mediastring'))

        for mobj in re.finditer(
                r'<a[^>]+\bclass=["\']downloadBtn\b[^>]+\bhref=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage):
            add_video_url(mobj.group('url'))

        upload_date = None
        formats = []

        def add_format(format_url, height=None):
            ext = determine_ext(format_url)
            if ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
                return
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                return
            if not height:
                height = int_or_none(self._search_regex(
                    r'(?P<height>\d+)[pP]?_\d+[kK]', format_url, 'height',
                    default=None))
            formats.append({
                'url': format_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
            })

        if not video_urls:
            # import here to avoid mutually recursive dependency
            from .generic import GenericIE
            ret = GenericIE.generic_url_result(url, video_id=video_id, video_title=title, force_videoid=True)
            ret['_type'] = 'url_transparent'
            return ret

        for video_url, height in video_urls:
            if not upload_date:
                upload_date = self._search_regex(
                    r'/(\d{6}/\d{2})/', video_url, 'upload data', default=None)
                if upload_date:
                    upload_date = upload_date.replace('/', '')
            if '/video/get_media' in video_url:
                # self._set_cookie(host, 'platform', 'tv')
                medias = self._download_json(video_url, video_id, fatal=False)
                for media in traverse_obj(medias, lambda _, v: v['videoUrl']):
                    video_url = url_or_none(media['videoUrl'])
                    if not video_url:
                        continue
                    height = int_or_none(media.get('quality'))
                    add_format(video_url, height)
                continue
            add_format(video_url)

        self._sort_formats(
            formats, field_preference=('height', 'width', 'fps', 'format_id'))

        model_profile = self._search_json(
            r'var\s+MODEL_PROFILE\s*=', webpage, 'model profile', video_id, fatal=False)
        video_uploader = self._html_search_regex(
            r'(?s)From:&nbsp;.+?<(?:a\b[^>]+\bhref=["\']/(?:(?:user|channel)s|model|pornstar)/|span\b[^>]+\bclass=["\']username)[^>]+>(.+?)<',
            webpage, 'uploader', default=None) or model_profile.get('username')

        def extract_vote_count(kind, name):
            return self._extract_count(
                (r'<span[^>]+\bclass="votes%s"[^>]*>(\d[\d,\.]*[kKmM]?)</span>' % kind,
                 r'<span[^>]+\bclass=["\']votes%s["\'][^>]*\bdata-rating=["\'](\d+)' % kind),
                webpage, name)

        view_count = self._extract_count(
            r'<span class="count">(\d[\d,\.]*[kKmM]?)</span> [Vv]iews', webpage, 'view')
        like_count = extract_vote_count('Up', 'like')
        dislike_count = extract_vote_count('Down', 'dislike')
        comment_count = self._extract_count(
            r'All Comments\s*<span>\((\d[\d,\.]*[kKmM]?)\)', webpage, 'comment')

        def extract_list(meta_key):
            div = self._search_regex(
                r'(?s)<div[^>]+\bclass=["\'].*?\b%sWrapper[^>]*>(.+?)</div>'
                % meta_key, webpage, meta_key, default=None)
            if div:
                return [clean_html(x) for x in re.findall(r'(?s)<a[^>]+\bhref=[^>]+>.+?</a>', div)]

        info = self._search_json_ld(webpage, video_id, default={})
        # description provided in JSON-LD is irrelevant
        for k in ('url', 'description'):
            info.pop(k, None)

        return merge_dicts(info, {
            'id': video_id,
            'uploader': video_uploader,
            'uploader_id': remove_start(model_profile.get('modelProfileLink'), '/model/'),
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
            'cast': extract_list('pornstars'),
            'subtitles': subtitles,
        })


class PornHubPlaylistBaseIE(PornHubBaseIE):
    def _extract_page(self, url):
        return int_or_none(self._search_regex(
            r'\bpage=(\d+)', url, 'page', default=None))

    def _extract_entries(self, webpage, host):
        # Only process container div with main playlist content skipping
        # drop-down menu that uses similar pattern for videos (see
        # https://github.com/ytdl-org/youtube-dl/issues/11594).
        container = self._search_regex(
            r'(?s)(<div\s[^>]*class=["\']container.+)', webpage,
            'container', default=webpage)

        def entries():
            seen_ids = set()
            for m in re.finditer(r'<\w+\s[^>]*(?<!-)\bhref\s*=\s*.("|\'|\b)%s\1[^>]*>' % (PornHubIE._PORNHUB_PATH_RE,), container):
                video_id = m.group('id')
                if video_id:
                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)
                elt = extract_attributes(m.group(0))
                video_url = urljoin(host, elt.get('href'))
                yield video_url, video_id, elt.get('title')

        return [
            self.url_result(
                video_url, PornHubIE.ie_key(), video_title=title, video_id=video_id)
            for video_url, video_id, title in entries()
        ]


class PornHubPagedPlaylistBaseIE(PornHubPlaylistBaseIE):
    @staticmethod
    def _has_more(webpage):
        return re.search(
            r'''(?x)
                <li[^>]+\bclass=["\']page_next|
                <link[^>]+\brel=["\']next|
                <button[^>]+\bid=["\']moreDataBtn
            ''', webpage) is not None

    def _entries(self, url, host, item_id):
        page = self._extract_page(url)

        VIDEOS = '/videos'

        def download_page(base_url, num, fallback=False):
            note = 'Downloading page %d%s' % (num, ' (switch to fallback)' if fallback else '')
            return self._download_webpage(
                base_url, item_id, note, query={'page': num})

        def is_404(e):
            return isinstance(e.cause, compat_HTTPError) and e.cause.code == 404

        base_url = url
        has_page = page is not None
        first_page = page if has_page else 1
        for page_num in (first_page, ) if has_page else itertools.count(first_page):
            try:
                try:
                    webpage = download_page(base_url, page_num)
                except ExtractorError as e:
                    # Some sources may not be available via /videos page,
                    # trying to fallback to main page pagination (see [1])
                    # 1. https://github.com/ytdl-org/youtube-dl/issues/27853
                    if is_404(e) and page_num == first_page and VIDEOS in base_url:
                        base_url = base_url.replace(VIDEOS, '')
                        webpage = download_page(base_url, page_num, fallback=True)
                    else:
                        raise
            except ExtractorError as e:
                if is_404(e) and page_num != first_page:
                    break
                raise
            page_entries = self._extract_entries(webpage, host)
            if not page_entries:
                break
            for from_ in page_entries:
                yield from_
            if not self._has_more(webpage):
                break

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        host = mobj.group('host')
        item_id = mobj.group('id')

        self._login(host)
        self._set_age_cookies(host)

        return self.playlist_result(self._entries(url, host, item_id), item_id)


class PornHubUserIE(PornHubPagedPlaylistBaseIE):
    _VALID_URL = r'(?P<url>https?://(?:[^/]+\.)?%s/(?P<id>(?:(?:user|channel)s|model|pornstar)/[^/?#&]+))(?:[?#&]|/(?!videos)|$)' % PornHubBaseIE._PORNHUB_HOST_RE
    _TESTS = [{
        'url': 'https://www.pornhub.com/model/zoe_ph',
        'info_dict': {
            'id': 'zoe_ph',
        },
        'playlist_mincount': 118,
    }, {
        'url': 'https://www.pornhub.com/pornstar/liz-vicious',
        'info_dict': {
            'id': 'liz-vicious',
        },
        'playlist_mincount': 118,
    }, {
        'url': 'https://www.pornhub.com/users/russianveet69',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/channels/povd',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/model/zoe_ph?abc=1',
        'only_matching': True,
    }, {
        # Unavailable via /videos page, but available with direct pagination
        # on pornstar page (see [1]), requires premium
        # 1. https://github.com/ytdl-org/youtube-dl/issues/27853
        'url': 'https://www.pornhubpremium.com/pornstar/sienna-west',
        'only_matching': True,
    }, {
        # Same as before, multi page
        'url': 'https://www.pornhubpremium.com/pornstar/lily-labeau',
        'only_matching': True,
    }, {
        'url': 'https://pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd.onion/model/zoe_ph',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        user_id, host = mobj.group('id', 'host')
        videos_url = '%s/videos' % mobj.group('url')
        page = self._extract_page(url)
        if page:
            videos_url = update_url_query(videos_url, {'page': page})

        self._login(host)

        return self.playlist_result(self._entries(videos_url, host, user_id), user_id.split('/')[-1])
        # return self.url_result(
        #     videos_url, ie=PornHubPagedVideoListIE.ie_key(), video_id=user_id)


class PornHubPagedVideoListIE(PornHubPagedPlaylistBaseIE):
    _VALID_URL = r'https?://(?:[^/]+\.)?%s/(?!playlist/|gif/)(?P<id>(?:[^/]+/)*[^/?#&]+)' % PornHubBaseIE._PORNHUB_HOST_RE
    _TESTS = [{
        'url': 'https://www.pornhub.com/model/zoe_ph/videos',
        'only_matching': True,
    }, {
        'url': 'http://www.pornhub.com/users/rushandlia/videos',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/pornstar/jenny-blighe/videos',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/pornstar/kylie-quinn/videos',
        'info_dict': {
            'id': 'pornstar/kylie-quinn/videos',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'https://www.pornhub.com/pornstar/kylie-quinn/videos?page=2',
        'info_dict': {
            'id': 'pornstar/kylie-quinn/videos',
        },
        # specific page: process just that page
        'playlist_count': 40,
    }, {
        # default sorting as Top Rated Videos
        'url': 'https://www.pornhub.com/channels/povd/videos',
        'info_dict': {
            'id': 'channels/povd/videos',
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
        # Most Viewed Videos
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos?o=mv',
        'only_matching': True,
    }, {
        # Top Rated Videos
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos?o=tr',
        'only_matching': True,
    }, {
        # Longest Videos
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos?o=lg',
        'only_matching': True,
    }, {
        # Newest Videos
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos?o=cm',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos/paid',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/pornstar/liz-vicious/videos/fanonly',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/video',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/video?page=3',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/video/search?search=123',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/categories/teen',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/categories/teen?page=3',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/hd',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/hd?page=3',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/described-video',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/described-video?page=2',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhub.com/video/incategories/60fps-1/hd-porn',
        'only_matching': True,
    }, {
        'url': 'https://pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd.onion/model/zoe_ph/videos',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return (not any(ph.suitable(url) for ph in (PornHubIE, PornHubUserIE, PornHubUserVideosUploadIE))
                and super(PornHubPagedVideoListIE, cls).suitable(url))


class PornHubUserVideosUploadIE(PornHubPagedPlaylistBaseIE):
    _VALID_URL = r'(?P<url>https?://(?:[^/]+\.)?%s/(?:(?:user|channel)s|model|pornstar)/(?P<id>[^/]+)/videos/upload)' % PornHubBaseIE._PORNHUB_HOST_RE
    _TESTS = [{
        'url': 'https://www.pornhub.com/pornstar/jenny-blighe/videos/upload',
        'info_dict': {
            'id': 'jenny-blighe',
        },
        'playlist_mincount': 129,
    }, {
        'url': 'https://www.pornhub.com/model/zoe_ph/videos/upload',
        'only_matching': True,
    }, {
        'url': 'http://pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd.onion/pornstar/jenny-blighe/videos/upload',
        'only_matching': True,
    }]


class PornHubPlaylistIE(PornHubPlaylistBaseIE):
    _VALID_URL = r'(?P<url>https?://(?:[^/]+\.)?%s/playlist/(?P<id>[^/?#&]+))' % PornHubBaseIE._PORNHUB_HOST_RE
    _TESTS = [{
        'url': 'https://www.pornhub.com/playlist/44121572',
        'info_dict': {
            'id': '44121572',
        },
        'playlist_mincount': 55,
    }, {
        'url': 'https://www.pornhub.com/playlist/4667351',
        'only_matching': True,
    }, {
        'url': 'https://de.pornhub.com/playlist/4667351',
        'only_matching': True,
    }, {
        'url': 'https://de.pornhub.com/playlist/4667351?page=2',
        'only_matching': True,
    }]

    def _entries(self, url, host, item_id):
        webpage = self._download_webpage(url, item_id, 'Downloading page 1')
        playlist_id = self._search_regex(r'var\s+playlistId\s*=\s*"([^"]+)"', webpage, 'playlist_id')
        video_count = int_or_none(
            self._search_regex(r'var\s+itemsCount\s*=\s*([0-9]+)\s*\|\|', webpage, 'video_count'))
        token = self._search_regex(r'var\s+token\s*=\s*"([^"]+)"', webpage, 'token')
        page_count = (video_count - 36 + 39) // 40 + 1
        page_entries = self._extract_entries(webpage, host)

        def download_page(page_num):
            note = 'Downloading page {0}'.format(page_num)
            page_url = 'https://www.{0}/playlist/viewChunked'.format(host)
            return self._download_webpage(page_url, item_id, note, query={
                'id': playlist_id,
                'page': page_num,
                'token': token,
            })

        for page_num in range(1, page_count + 1):
            if page_num > 1:
                webpage = download_page(page_num)
                page_entries = self._extract_entries(webpage, host)
            if not page_entries:
                break
            for from_ in page_entries:
                yield from_

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        host, item_id = mobj.group('host', 'id')

        self._login(host)
        self._set_age_cookies(host)

        return self.playlist_result(self._entries(mobj.group('url'), host, item_id), item_id)

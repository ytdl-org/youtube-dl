# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from math import isinf

from .common import InfoExtractor, SearchInfoExtractor
from ..compat import (
    compat_kwargs,
    compat_urlparse,
)
from ..utils import (
    classpropinit,
    clean_html,
    determine_ext,
    extract_attributes,
    ExtractorError,
    float_or_none,
    int_or_none,
    join_nonempty,
    merge_dicts,
    parse_duration,
    parse_qs,
    T,
    traverse_obj,
    txt_or_none,
    unified_strdate,
    url_or_none,
    urljoin,
)


class XHamsterBaseIE(InfoExtractor):
    # base domains that don't redirect to xhamster.com (not xhday\d\.com, eg)
    _DOMAINS = '(?:%s)' % '|'.join((
        r'xhamster\d*\.(?:com|desi)',
        r'xhamster\.one',
        r'xhms\.pro',
        r'xh(?:open|access|victory|big|channel)\.com',
        r'(?:full|mega)xh\.com',
        r'xh(?:vid|official|planet)\d*\.com',
        # requires Tor
        r'xhamster[a-z2-7]+\.onion',
    ))

    def _download_webpage_handle(self, url, video_id, *args, **kwargs):
        # note=None, errnote=None, fatal=True, encoding=None, data=None, headers={}, query={}, expected_status=None)
        # default UA to 'Mozilla' (only) to avoid interstitial page
        headers = (args[5] if len(args) > 5 else kwargs.get('headers'))
        if 'User-Agent' not in (headers or {}):
            if len(args) > 5:
                args = list(args)
                headers = headers or {}
                args[5] = headers
            elif not isinstance(headers, dict):
                headers = {}
            headers['User-Agent'] = 'Mozilla'
            if len(args) <= 5:
                if not kwargs.get('headers'):
                    kwargs['headers'] = headers
                kwargs = compat_kwargs(kwargs)
        return super(XHamsterBaseIE, self)._download_webpage_handle(
            url, video_id, *args, **kwargs)


class XHamsterIE(XHamsterBaseIE):
    _VALID_URL = classpropinit(
        lambda cls:
            r'''(?x)
                https?://
                    (?:.+?\.)?%s/
                    (?:
                        movies/(?P<id>[\dA-Za-z]+)/(?P<display_id>[^/]*)\.html|
                        videos/(?P<display_id_2>[^/]*)-(?P<id_2>[\dA-Za-z]+)
                    )
            ''' % cls._DOMAINS)
    _TESTS = [{
        'url': 'https://xhamster.com/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'md5': '34e1ab926db5dc2750fed9e1f34304bb',
        'info_dict': {
            'id': '1509445',
            'display_id': 'femaleagent-shy-beauty-takes-the-bait',
            'ext': 'mp4',
            'title': 'FemaleAgent Shy beauty takes the bait',
            'timestamp': 1350194821,
            'upload_date': '20121014',
            'uploader': 'Ruseful2011',
            'uploader_id': 'ruseful2011',
            'duration': 893,
            'age_limit': 18,
        },
    }, {
        'url': 'https://xhamster.com/videos/britney-spears-sexy-booty-2221348?hd=',
        'info_dict': {
            'id': '2221348',
            'display_id': 'britney-spears-sexy-booty',
            'ext': 'mp4',
            'title': 'Britney Spears  Sexy Booty',
            'timestamp': 1379123460,
            'upload_date': '20130914',
            'uploader': 'jojo747400',
            'duration': 200,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # empty seo, unavailable via new URL schema
        'url': 'http://xhamster.com/movies/5667973/.html',
        'info_dict': {
            'id': '5667973',
            'ext': 'mp4',
            'title': '....',
            'timestamp': 1454948101,
            'upload_date': '20160208',
            'uploader': 'parejafree',
            'uploader_id': 'parejafree',
            'duration': 72,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # mobile site
        'url': 'https://m.xhamster.com/videos/cute-teen-jacqueline-solo-masturbation-8559111',
        'only_matching': True,
    }, {
        'url': 'https://xhamster.com/movies/2272726/amber_slayed_by_the_knight.html',
        'only_matching': True,
    }, {
        # This video is visible for marcoalfa123456's friends only
        'url': 'https://it.xhamster.com/movies/7263980/la_mia_vicina.html',
        'only_matching': True,
    }, {
        # new URL schema
        'url': 'https://pt.xhamster.com/videos/euro-pedal-pumping-7937821',
        'only_matching': True,
    }, {
        'url': 'https://xhamster.one/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'only_matching': True,
    }, {
        'url': 'https://xhamster.desi/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'only_matching': True,
    }, {
        'url': 'https://xhamster2.com/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'only_matching': True,
    }, {
        'url': 'https://xhamster11.com/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'only_matching': True,
    }, {
        'url': 'https://xhamster26.com/videos/femaleagent-shy-beauty-takes-the-bait-1509445',
        'only_matching': True,
    }, {
        'url': 'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
        'only_matching': True,
    }, {
        'url': 'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
        'only_matching': True,
    }, {
        'url': 'http://de.xhamster.com/videos/skinny-girl-fucks-herself-hard-in-the-forest-xhnBJZx',
        'only_matching': True,
    }, {
        # 'url': 'https://xhday.com/videos/strapless-threesome-xhh7yVf',
        'url': 'https://xhvid.com/videos/lk-mm-xhc6wn6',
        'only_matching': True,
    }]

    def _get_height(self, s):
        return int_or_none(self._search_regex(
            r'^(\d+)[pP]', s, 'height', default=None))

    def _extract_initials(self, initials, video_id, display_id, url, referrer, age_limit):
        video = initials['videoModel']
        title = video['title']
        formats = []
        format_urls = set()
        format_sizes = {}
        http_headers = {'Referer': referrer}
        for quality, size in traverse_obj(video, (
                'sources', 'download', T(dict.items), Ellipsis,
                T(lambda kv: (kv[0], float_or_none(kv[1]['size']))),
                T(lambda kv: (kv[1] is not None) and kv))):
            format_sizes[quality] = size
        # Download link takes some time to be generated,
        # skipping for now
        for format_id, formats_dict in traverse_obj(video, (
                'sources', T(dict.items),
                lambda _, kv: kv[0] != 'download' and isinstance(kv[1], dict))):
            for quality, format_url in traverse_obj(formats_dict, (
                    T(dict.items), Ellipsis,
                    T(lambda kv: (kv[0], url_or_none(kv[1]))))):
                if format_url in format_urls:
                    continue
                format_urls.add(format_url)
                formats.append({
                    'format_id': '%s-%s' % (format_id, quality),
                    'url': format_url,
                    'ext': determine_ext(format_url, 'mp4'),
                    'height': self._get_height(quality),
                    'filesize': format_sizes.get(quality),
                    'http_headers': http_headers,
                })
        xplayer_sources = traverse_obj(
            initials, ('xplayerSettings', 'sources', T(dict)))
        for hls_url in traverse_obj(
                xplayer_sources,
                ('hls', ('url', 'fallback'), T(lambda u: urljoin(url, u)))):
            if hls_url in format_urls:
                continue
            format_urls.add(hls_url)
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False))
        for format_id, formats_list in traverse_obj(
                xplayer_sources, ('standard', T(dict.items), Ellipsis)):
            for standard_format in traverse_obj(formats_list, Ellipsis):
                for standard_url in traverse_obj(
                        standard_format,
                        (('url', 'fallback'), T(lambda u: urljoin(url, u)))):
                    format_urls.add(standard_url)
                    ext = determine_ext(standard_url, 'mp4')
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            standard_url, video_id, 'mp4', entry_protocol='m3u8_native',
                            m3u8_id='hls', fatal=False))
                    else:
                        quality = traverse_obj(standard_format, (('quality', 'label'), T(txt_or_none)), get_all=False) or ''
                        formats.append({
                            'format_id': '%s-%s' % (format_id, quality),
                            'url': standard_url,
                            'ext': ext,
                            'height': self._get_height(quality),
                            'filesize': format_sizes.get(quality),
                            'http_headers': {
                                'Referer': standard_url,
                            },
                        })
        self._sort_formats(
            formats, field_preference=('height', 'width', 'tbr', 'format_id'))

        categories = traverse_obj(video, ('categories', Ellipsis, 'name', T(txt_or_none))) or None
        uploader_url = traverse_obj(video, ('author', 'pageURL', T(url_or_none)))

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'uploader_url': uploader_url,
            'uploader_id': uploader_url.split('/')[-1] if uploader_url else None,
            'age_limit': age_limit if age_limit is not None else 18,
            'categories': categories,
            'formats': formats,
        }, traverse_obj(video, {
            'description': ('description', T(txt_or_none)),
            'timestamp': ('created', T(int_or_none)),
            'uploader': ('author', 'name', T(txt_or_none)),
            'thumbnail': ('thumbURL', T(url_or_none)),
            'duration': ('duration', T(int_or_none)),
            'view_count': ('views', T(int_or_none)),
            'like_count': ('rating', 'likes', T(int_or_none)),
            'dislike_count': ('rating', 'dislikes', T(int_or_none)),
            'comment_count': ('comments', T(int_or_none)),
        }))

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = traverse_obj(mobj, 'id', 'id_2')
        display_id = traverse_obj(mobj, 'display_id', 'display_id_2')

        desktop_url = re.sub(r'^(https?://(?:.+?\.)?)m\.', r'\1', url)
        webpage, urlh = self._download_webpage_handle(desktop_url, video_id)

        error = self._html_search_regex(
            r'<div[^>]+id=["\']videoClosed["\'][^>]*>(.+?)</div>',
            webpage, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)

        age_limit = self._rta_search(webpage)

        initials = self._parse_json(
            self._search_regex(
                (r'window\.initials\s*=\s*({.+?})\s*;\s*</script>',
                 r'window\.initials\s*=\s*({.+?})\s*;'), webpage, 'initials',
                default='{}'),
            video_id, fatal=False)

        if initials:
            return self._extract_initials(initials, video_id, display_id, url, urlh.geturl, age_limit)

        return self._old_real_extract(webpage, video_id, display_id, age_limit)

    def _old_real_extract(self, webpage, video_id, display_id, age_limit):

        # Old layout fallback

        title = self._html_search_regex(
            [r'<h1[^>]*>([^<]+)</h1>',
             r'<meta[^>]+itemprop=".*?caption.*?"[^>]+content="(.+?)"',
             r'<title[^>]*>(.+?)(?:,\s*[^,]*?\s*Porn\s*[^,]*?:\s*xHamster[^<]*| - xHamster\.com)</title>'],
            webpage, 'title')

        formats = []
        format_urls = set()

        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})\s*,?\s*\n', webpage, 'sources',
                default='{}'),
            video_id, fatal=False)
        for format_id, format_url in traverse_obj(sources, (
                T(dict.items), Ellipsis,
                T(lambda kv: (kv[0], url_or_none(kv[1]))),
                T(lambda kv: kv[1] and kv))):
            if format_url in format_urls:
                continue
            format_urls.add(format_url)
            formats.append({
                'format_id': format_id,
                'url': format_url,
                'height': self._get_height(format_id),
            })

        video_url = self._search_regex(
            [r'''file\s*:\s*(?P<q>["'])(?P<mp4>.+?)(?P=q)''',
             r'''<a\s+href=(?P<q>["'])(?P<mp4>.+?)(?P=q)\s+class=["']mp4Thumb''',
             r'''<video[^>]+file=(?P<q>["'])(?P<mp4>.+?)(?P=q)[^>]*>'''],
            webpage, 'video url', group='mp4', default=None)
        if video_url and video_url not in format_urls:
            formats.append({
                'url': video_url,
            })

        self._sort_formats(formats)

        uploader = self._html_search_regex(
            r'<span[^>]+itemprop=["\']author[^>]+><a[^>]+><span[^>]+>([^<]+)',
            webpage, 'uploader', default='anonymous')

        categories = [clean_html(category) for category in re.findall(
            r'<a[^>]+>(.+?)</a>', self._search_regex(
                r'(?s)<table.+?(<span>Categories:.+?)</table>', webpage,
                'categories', default=''))]

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            # Only a few videos have a description
            'description': traverse_obj(
                re.search(r'<span>Description:\s*</span>([^<]+)', webpage), 1),
            'upload_date': unified_strdate(self._search_regex(
                r'hint=["\'](\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} [A-Z]{3,4}',
                webpage, 'upload date', fatal=False)),
            'uploader': uploader,
            'uploader_id': (uploader or '').lower() or None,
            'thumbnail': url_or_none(self._search_regex(
                (r'''["']thumbUrl["']\s*:\s*(?P<q>["'])(?P<thumbnail>.+?)(?P=q)''',
                 r'''<video[^>]+"poster"=(?P<q>["'])(?P<thumbnail>.+?)(?P=q)[^>]*>'''),
                webpage, 'thumbnail', fatal=False, group='thumbnail')),
            'duration': parse_duration(self._search_regex(
                (r'<[^<]+\bitemprop=["\']duration["\'][^<]+\bcontent=["\'](.+?)["\']',
                 r'Runtime:\s*</span>\s*([\d:]+)'), webpage,
                'duration', fatal=False)),
            'view_count': int_or_none(self._search_regex(
                r'content=["\']User(?:View|Play)s:\s*(\d+)',
                webpage, 'view count', fatal=False)),
            'comment_count': traverse_obj(
                re.search(r'</label>Comments \((?P<commentcount>\d+)\)</div>', webpage),
                ('commentcount', T(int_or_none))),
            'age_limit': age_limit,
            'categories': categories or None,
            'formats': formats,
        }, traverse_obj(
            re.search(r'hint=[\'"](?P<likecount>\d+) Likes / (?P<dislikecount>\d+) Dislikes', webpage), {
                'like_count': ('likecount', T(int_or_none)),
                'dislike_count': ('dislikecount', T(int_or_none)),
            }))


class XHamsterEmbedIE(XHamsterBaseIE):
    _VALID_URL = classpropinit(
        lambda cls:
        r'https?://(?:.+?\.)?%s/xembed\.php\?video=(?P<id>\d+)' % cls._DOMAINS)
    _TEST = {
        'url': 'http://xhamster.com/xembed.php?video=3328539',
        'info_dict': {
            'id': '3328539',
            'ext': 'mp4',
            'title': 'Pen Masturbation',
            'timestamp': 1406581861,
            'upload_date': '20140728',
            'uploader': 'ManyakisArt',
            'uploader_id': 'manyakisart',
            'duration': 5,
            'age_limit': 18,
        }
    }

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?xhamster\.com/xembed\.php\?video=\d+)\1',
            webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'href="(https?://xhamster\.com/(?:movies/{0}/[^"]*\.html|videos/[^/]*-{0})[^"]*)"'.format(video_id),
            webpage, 'xhamster url', default=None)

        if not video_url:
            vars = self._parse_json(
                self._search_regex(r'vars\s*:\s*({.+?})\s*,\s*\n', webpage, 'vars'),
                video_id)
            video_url = traverse_obj(vars, 'downloadLink', 'homepageLink', 'commentsLink', 'shareUrl', expected_type=url_or_none)

        return self.url_result(video_url, 'XHamster')


class XHamsterPlaylistIE(XHamsterBaseIE):
    _NEXT_PAGE_RE = r'(<a\b[^>]+\bdata-page\s*=\s*["\']next[^>]+>)'
    _VALID_URL_TPL = r'''(?x)
        https?://(?:.+?\.)?%s
                /%s/(?P<id>[^/?#]+)
                (?:(?P<sub>(?:/%s)+))?
                (?:/(?P<pnum>\d+))?(?:[/?#]|$)
    '''

    def _page_url(self, user_id, page_num, url=None):
        return self._PAGE_URL_TPL % (user_id, page_num)

    def _extract_entries(self, page, user_id):
        for video_tag_match in re.finditer(
                r'<a[^>]+class=["\'].*?\bvideo-thumb__image-container[^>]+>',
                page):
            video_url = traverse_obj(video_tag_match, (
                0, T(extract_attributes), 'href', T(url_or_none)))
            if not video_url or not XHamsterIE.suitable(video_url):
                continue
            video_id = XHamsterIE._match_id(video_url)
            yield self.url_result(
                video_url, ie=XHamsterIE.ie_key(), video_id=video_id)

    def _next_page_url(self, page, user_id, page_num):
        return traverse_obj(
            self._search_regex(self._NEXT_PAGE_RE, page, 'next page', default=None),
            (T(extract_attributes), 'href', T(url_or_none)))

    def _entries(self, user_id, page_num=None, page=None, url=None):
        page_1 = 1 if page_num is None else page_num
        next_page_url = self._page_url(user_id, page_1, url)
        for pagenum in itertools.count(page_1):
            if not page:
                page = self._download_webpage(
                    next_page_url, user_id, 'Downloading page' + ((' %d' % pagenum) if pagenum > 1 else ''),
                    fatal=False)
            if not page:
                break

            for from_ in self._extract_entries(page, user_id):
                yield from_

            if page_num is not None:
                break
            next_page_url = self._next_page_url(page, user_id, page_num)
            if not next_page_url:
                break
            page = None

    def _fancy_page_url(self, user_id, page_num, url):
        sub = self._match_valid_url(url).group('sub')
        n_url = self._PAGE_URL_TPL % (
            join_nonempty(user_id, sub, delim='/'), page_num)
        return compat_urlparse.urljoin(n_url, url)

    def _fancy_get_title(self, user_id, page_num, url):
        sub = self._match_valid_url(url).group('sub')
        sub = (sub or '').split('/')
        sub.extend((compat_urlparse.urlsplit(url).query or '').split('&'))
        sub.append('all' if page_num is None else ('p%d' % page_num))
        return '%s (%s)' % (user_id, join_nonempty(*sub, delim=','))

    @staticmethod
    def _get_title(user_id, page_num, url=None):
        return '%s (%s)' % (user_id, 'all' if page_num is None else ('p%d' % page_num))

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        user_id = mobj.group('id')
        page_num = int_or_none(mobj.groupdict().get('pnum'))
        return self.playlist_result(
            self._entries(user_id, page_num, url=url), user_id,
            self._get_title(user_id, page_num, url=url))


class XHamsterUserIE(XHamsterPlaylistIE):
    _VALID_URL = classpropinit(
        lambda cls:
        r'https?://(?:.+?\.)?%s/users/(?P<id>[^/?#&]+)(?P<sub>/favorites)?(?:/videos/(?P<pnum>\d+))?' % cls._DOMAINS)
    _PAGE_URL_TPL = 'https://xhamster.com/users/%s/videos/%s'
    _TESTS = [{
        # Paginated user profile
        'url': 'https://xhamster.com/users/netvideogirls/videos',
        'info_dict': {
            'id': 'netvideogirls',
            'title': 'netvideogirls (all)',
        },
        'playlist_mincount': 267,
    }, {
        # Page from paginated user profile
        'url': 'https://xhamster.com/users/netvideogirls/videos/2',
        'info_dict': {
            'id': 'netvideogirls',
            'title': 'netvideogirls (p2)',
        },
        'playlist_count': 30,
    }, {
        # Non-paginated user profile
        'url': 'https://xhamster.com/users/firatkaan/videos',
        'info_dict': {
            'id': 'firatkaan',
            'title': 'firatkaan (all)',
        },
        'playlist_mincount': 1,
    }, {
        # User with `favorites`
        'url': 'https://xhamster.com/users/cubafidel/videos/',
        'info_dict': {
            'id': 'cubafidel',
            'title': 'cubafidel (all)',
        },
        'playlist_maxcount': 300,
    }, {
        # Faves of user with `favorites`
        'url': 'https://xhamster.com/users/cubafidel/favorites/videos/',
        'info_dict': {
            'id': 'cubafidel',
            'title': 'cubafidel (favorites,all)',
        },
        'playlist_mincount': 400,
    }, {
        # below URL doesn't match but is redirected via generic
        # 'url': 'https://xhday.com/users/mobhunter',
        'url': 'https://xhvid.com/users/pelushe21',
        'only_matching': True,
    }]


class XHamsterCreatorIE(XHamsterPlaylistIE):
    # `pornstars`, `celebrities` and `creators` share the same namespace
    _VALID_URL = classpropinit(
        lambda cls:
        cls._VALID_URL_TPL % (
            cls._DOMAINS,
            '(?:(?:gay|shemale)/)?(?:creators|pornstars|celebrities)',
            r'(?:hd|4k|newest|full-length|exclusive|best(?:/(?:weekly|monthly|year-\d{4}))?)',
        ))
    _PAGE_URL_TPL = 'https://xhamster.com/creators/%s/%s'
    _TESTS = [{
        # Paginated creator profile
        'url': 'https://xhamster.com/creators/mini-elfie',
        'info_dict': {
            'id': 'mini-elfie',
            'title': 'mini-elfie (all)',
        },
        'playlist_mincount': 70,
    }, {
        # Paginated pornstar profile
        'url': 'https://xhamster.com/pornstars/mariska-x',
        'info_dict': {
            'id': 'mariska-x',
            'title': 'mariska-x (all)',
        },
        'playlist_mincount': 163,
    }, {
        # creator profile filtered by path
        'url': 'https://xhamster.com/creators/mini-elfie/4k',
        'info_dict': {
            'id': 'mini-elfie',
            'title': 'mini-elfie (4k,all)',
        },
        'playlist_mincount': 5,
        'playlist_maxcount': 30,
    }, {
        # creator profile filtered by query
        'url': 'https://xhamster.com/creators/mini-elfie/?category=pov',
        'info_dict': {
            'id': 'mini-elfie',
            'title': 'mini-elfie (category=pov,all)',
        },
        'playlist_mincount': 8,
        'playlist_maxcount': 30,
    }]

    def _page_url(self, user_id, page_num, url):
        return self._fancy_page_url(user_id, page_num, url)

    def _get_title(self, user_id, page_num, url):
        return self._fancy_get_title(user_id, page_num, url)


class XHamsterCategoryIE(XHamsterPlaylistIE):
    # `tags` and `categories` share the same namespace
    _VALID_URL = classpropinit(
        lambda cls:
        cls._VALID_URL_TPL % (
            cls._DOMAINS,
            '(?:(?P<queer>gay|shemale)/)?(?:categories|tags|(?=hd))',
            r'(?:hd|4k|producer|creator|best(?:/(?:weekly|monthly|year-\d{4}))?)',
        ))
    _PAGE_URL_TPL = 'https://xhamster.com/categories/%s/%s'
    _NEXT_PAGE_RE = r'(<a\b[^>]+\bclass\s*=\s*("|\')(?:[\w-]+\s+)*?prev-next-list-link--next(?:\s+[\w-]+)*\2[^>]+>)'
    _TESTS = [{
        # Paginated category/tag
        'url': 'https://xhamster.com/tags/hawaiian',
        'info_dict': {
            'id': 'hawaiian',
            'title': 'hawaiian (all)',
        },
        'playlist_mincount': 250,
    }, {
        # Single page category/tag
        'url': 'https://xhamster.com/categories/aruban',
        'info_dict': {
            'id': 'aruban',
            'title': 'aruban (all)',
        },
        'playlist_mincount': 5,
        'playlist_maxcount': 30,
    }, {
        # category/tag filtered by path
        'url': 'https://xhamster.com/categories/hawaiian/4k',
        'info_dict': {
            'id': 'hawaiian',
            'title': 'hawaiian (4k,all)',
        },
        'playlist_mincount': 1,
        'playlist_maxcount': 20,
    }, {
        # category/tag filtered by query
        'url': 'https://xhamster.com/tags/hawaiian?fps=60',
        'info_dict': {
            'id': 'hawaiian',
            'title': 'hawaiian (fps=60,all)',
        },
        'playlist_mincount': 1,
        'playlist_maxcount': 20,
    }]

    def _page_url(self, user_id, page_num, url):
        queer, sub = self._match_valid_url(url).group('queer', 'sub')
        n_url = self._PAGE_URL_TPL % (
            join_nonempty(queer, user_id, sub, delim='/'), page_num)
        return compat_urlparse.urljoin(n_url, url)

    def _get_title(self, user_id, page_num, url):
        queer, sub = self._match_valid_url(url).group('queer', 'sub')
        queer = [] if queer is None else [queer]
        sub = queer + (sub or '').split('/')
        sub.extend((compat_urlparse.urlsplit(url).query or '').split('&'))
        sub.append('all' if page_num is None else ('p%d' % page_num))
        return '%s (%s)' % (user_id, join_nonempty(*sub, delim=','))


class XHamsterSearchIE(XHamsterPlaylistIE):
    _VALID_URL = classpropinit(
        lambda cls:
        r'''(?x)
            https?://(?:.+?\.)?%s
                    /search/(?P<id>[^/?#]+)
        ''' % cls._DOMAINS)
    _TESTS = [{
        # Single page result
        'url': 'https://xhamster.com/search/latvia',
        'info_dict': {
            'id': 'latvia',
            'title': 'latvia (all)',
        },
        'playlist_mincount': 10,
        'playlist_maxcount': 30,
    }, {
        # Paginated result
        'url': 'https://xhamster.com/search/latvia+estonia+moldova+lithuania',
        'info_dict': {
            'id': 'latvia+estonia+moldova+lithuania',
            'title': 'latvia estonia moldova lithuania (all)',
        },
        'playlist_mincount': 63,
    }, {
        # Single page of paginated result
        'url': 'https://xhamster.com/search/latvia+estonia+moldova+lithuania?page=2',
        'info_dict': {
            'id': 'latvia+estonia+moldova+lithuania',
            'title': 'latvia estonia moldova lithuania (p2)',
        },
        'playlist_count': 47,
    }]

    @staticmethod
    def _page_url(user_id, page_num, url):
        return url

    def _get_title(self, user_id, page_num, url=None):
        return super(XHamsterSearchIE, self)._get_title(
            user_id.replace('+', ' '), page_num, url)

    def _real_extract(self, url):
        user_id = self._match_id(url)
        page_num = traverse_obj(url, (
            T(parse_qs), 'page', -1, T(int_or_none)))
        return self.playlist_result(
            self._entries(user_id, page_num, url=url), user_id,
            self._get_title(user_id, page_num))


class XHamsterSearchKeyIE(SearchInfoExtractor, XHamsterSearchIE):
    _SEARCH_KEY = 'xhsearch'
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        # Single page result
        'url': 'xhsearchall:latvia',
        'info_dict': {
            'id': 'latvia',
            'title': 'latvia (all)',
        },
        'playlist_mincount': 10,
        'playlist_maxcount': 30,
    }, {
        # Paginated result
        'url': 'xhsearchall:latvia estonia moldova lithuania',
        'info_dict': {
            'id': 'latvia+estonia+moldova+lithuania',
            'title': 'latvia estonia moldova lithuania (all)',
        },
        'playlist_mincount': 63,
    }, {
        # Subset of paginated result
        'url': 'xhsearch50:latvia estonia moldova lithuania',
        'info_dict': {
            'id': 'latvia+estonia+moldova+lithuania',
            'title': 'latvia estonia moldova lithuania (first 50)',
        },
        'playlist_count': 50,
    }]

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        result = XHamsterSearchIE._real_extract(
            self, 'https://xhamster.com/search/' + query.replace(' ', '+'))

        if not isinf(n):
            # with the secret knowledge that `result['entries'] is a
            # generator, it can be sliced efficiently
            result['entries'] = itertools.islice(result['entries'], n)
            if result.get('title') is not None:
                result['title'] = result['title'].replace('(all)', '(first %d)' % n)

        return result

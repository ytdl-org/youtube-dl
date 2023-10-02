# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..compat import (
    compat_kwargs,
    compat_urlparse,
)
from ..utils import (
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
    _VALID_URL = r'''(?x)
                    https?://
                        (?:.+?\.)?%s/
                        (?:
                            movies/(?P<id>[\dA-Za-z]+)/(?P<display_id>[^/]*)\.html|
                            videos/(?P<display_id_2>[^/]*)-(?P<id_2>[\dA-Za-z]+)
                        )
                    ''' % _DOMAINS
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
    _VALID_URL = r'https?://(?:.+?\.)?%s/xembed\.php\?video=(?P<id>\d+)' % XHamsterIE._DOMAINS
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


class XHamsterUserIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?%s/users/(?P<id>[^/?#&]+)' % XHamsterIE._DOMAINS
    _TESTS = [{
        # Paginated user profile
        'url': 'https://xhamster.com/users/netvideogirls/videos',
        'info_dict': {
            'id': 'netvideogirls',
        },
        'playlist_mincount': 267,
    }, {
        # Non-paginated user profile
        'url': 'https://xhamster.com/users/firatkaan/videos',
        'info_dict': {
            'id': 'firatkaan',
        },
        'playlist_mincount': 1,
    }, {
        # the below doesn't match but is redirected via generic
        # 'url': 'https://xhday.com/users/mobhunter',
        'url': 'https://xhvid.com/users/pelushe21',
        'only_matching': True,
    }]

    def _entries(self, user_id):
        next_page_url = 'https://xhamster.com/users/%s/videos/1' % user_id
        for pagenum in itertools.count(1):
            page = self._download_webpage(
                next_page_url, user_id, 'Downloading page %s' % pagenum)
            for video_tag in re.findall(
                    r'(<a[^>]+class=["\'].*?\bvideo-thumb__image-container[^>]+>)',
                    page):
                video = extract_attributes(video_tag)
                video_url = url_or_none(video.get('href'))
                if not video_url or not XHamsterIE.suitable(video_url):
                    continue
                video_id = XHamsterIE._match_id(video_url)
                yield self.url_result(
                    video_url, ie=XHamsterIE.ie_key(), video_id=video_id)
            mobj = re.search(r'<a[^>]+data-page=["\']next[^>]+>', page)
            if not mobj:
                break
            next_page = extract_attributes(mobj.group(0))
            next_page_url = url_or_none(next_page.get('href'))
            if not next_page_url:
                break

    def _real_extract(self, url):
        user_id = self._match_id(url)
        return self.playlist_result(self._entries(user_id), user_id)

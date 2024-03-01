# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    str_to_int,
    merge_dicts,
    T,
    traverse_obj,
    unified_strdate,
    url_or_none,
)


class YouPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youporn\.com/(?:watch|embed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#&]+))?'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>(?:https?:)?//(?:www\.)?youporn\.com/embed/\d+)']
    _TESTS = [{
        'url': 'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'md5': '3744d24c50438cf5b6f6d59feb5055c2',
        'info_dict': {
            'id': '505835',
            'display_id': 'sex-ed-is-it-safe-to-masturbate-daily',
            'ext': 'mp4',
            'title': 'Sex Ed: Is It Safe To Masturbate Daily?',
            'description': 'Love & Sex Answers: http://bit.ly/DanAndJenn -- Is It Unhealthy To Masturbate Daily?',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 210,
            'uploader': 'Ask Dan And Jennifer',
            'upload_date': '20101217',
            'average_rating': int,
            'view_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
        'skip': 'This video has been disabled',
    }, {
        # Unknown uploader
        'url': 'http://www.youporn.com/watch/561726/big-tits-awesome-brunette-on-amazing-webcam-show/?from=related3&al=2&from_id=561726&pos=4',
        'info_dict': {
            'id': '561726',
            'display_id': 'big-tits-awesome-brunette-on-amazing-webcam-show',
            'ext': 'mp4',
            'title': 'Big Tits Awesome Brunette On amazing webcam show',
            'description': 'http://sweetlivegirls.com Big Tits Awesome Brunette On amazing webcam show.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Unknown',
            'upload_date': '20110418',
            'average_rating': int,
            'view_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
        'skip': '404',
    }, {
        'url': 'https://www.youporn.com/embed/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'only_matching': True,
    }, {
        'url': 'http://www.youporn.com/watch/505835',
        'only_matching': True,
    }, {
        'url': 'https://www.youporn.com/watch/13922959/femdom-principal/',
        'only_matching': True,
    }, {
        'url': 'https://www.youporn.com/watch/16290308/tinderspecial-trailer1/',
        'info_dict': {
            'id': '46949121',
            'age_limit': 18,
            'categories': [],
            'description': None,  # SEO spam using title removed
            'display_id': 'tinderspecial-trailer1',
            'duration': 298.0,
            'ext': 'mp4',
            'upload_date': '20201123',
            'uploader': 'Ersties',
            'tags': [],
            'thumbnail': 'https://fi1.ypncdn.com/m=eaSaaTbWx/202011/23/16290308/original/3.jpg',
            'timestamp': 1606147564,
            'title': 'Tinder In Real Life',
            'view_count': int,
        }
    }]

    @classmethod
    def _extract_urls(cls, webpage):
        def yield_urls():
            for p in cls._EMBED_REGEX:
                for m in re.finditer(p, webpage):
                    yield m.group('url')

        return list(yield_urls())

    def _real_extract(self, url):
        display_id = self._match_valid_url(url).group('id', 'display_id')
        url = 'http://www.youporn.com/watch/%s' % (display_id[0],)
        display_id = display_id[1] or display_id[0]
        webpage = self._download_webpage(
            url, display_id, headers={'Cookie': 'age_verified=1'})
        video_id = display_id[0]

        playervars = self._search_json(
            r'\bplayervars\s*:', webpage, 'playervars', display_id)

        def get_fmt(x):
            v_url = url_or_none(x.get('videoUrl'))
            if v_url:
                x['videoUrl'] = v_url
                return (x['format'], x)

        defs_by_format = dict(traverse_obj(playervars, (
            'mediaDefinitions', lambda _, v: v.get('format'), T(get_fmt))))

        def get_format_data(f):
            if f not in defs_by_format:
                return []
            return self._download_json(
                defs_by_format[f]['videoUrl'], display_id, '{0}-formats'.format(f))

        formats = []
        # Try to extract only the actual master m3u8 first, avoiding the duplicate single resolution "master" m3u8s
        for hls_url in traverse_obj(
                get_format_data('hls'),
                (lambda _, v: not isinstance(v['defaultQuality'], bool), 'videoUrl'),
                (Ellipsis, 'videoUrl')):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', fatal=False, m3u8_id='hls',
                entry_protocol='m3u8_native'))

        for f in traverse_obj(get_format_data('mp4'), (
                lambda _, v: v.get('videoUrl'), {
                    'url': ('videoUrl', T(url_or_none)),
                    'filesize': ('videoSize', T(int_or_none)),
                    'height': ('quality', T(int_or_none)),
                }, T(lambda x: x.get('videoUrl') and x))):
            # Video URL's path looks like this:
            #  /201012/17/505835/720p_1500k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            #  /201012/17/505835/vl_240p_240k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            #  /videos/201703/11/109285532/1080P_4000K_109285532.mp4
            # We will benefit from it by extracting some metadata
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', f['videoUrl'])
            if mobj:
                if not f.get('height'):
                    f['height'] = int(mobj.group('height'))
                f['tbr'] = int(mobj.group('bitrate'))
                f['format_id'] = '%dp-%dk' % (f['height'], f['tbr'])
            formats.append(f)
        self._sort_formats(formats)

        title = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']watchVideoTitle[^>]+>(.+?)</div>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'title', webpage, fatal=True)

        description = self._html_search_regex(
            r'(?s)<div[^>]+\bid=["\']description["\'][^>]*>(.+?)</div>',
            webpage, 'description',
            default=None) or self._og_search_description(
            webpage, default=None)
        thumbnail = self._search_regex(
            r'(?:imageurl\s*=|poster\s*:)\s*(["\'])(?P<thumbnail>.+?)\1',
            webpage, 'thumbnail', fatal=False, group='thumbnail')
        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'duration', fatal=False))

        uploader = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']submitByLink["\'][^>]*>(.+?)</div>',
            webpage, 'uploader', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            (r'UPLOADED:\s*<span>([^<]+)',
             r'Date\s+[Aa]dded:\s*<span>([^<]+)',
             r'''(?s)<div[^>]+class=["']videoInfo(?:Date|Time)\b[^>]*>(.+?)</div>''',
             r'(?s)<label\b[^>]*>Uploaded[^<]*</label>\s*<span\b[^>]*>(.+?)</span>'),
            webpage, 'upload date', fatal=False))

        age_limit = self._rta_search(webpage)

        view_count = None
        views = self._search_regex(
            r'(<div[^>]+\bclass=["\']js_videoInfoViews["\']>)', webpage,
            'views', default=None)
        if views:
            view_count = str_to_int(extract_attributes(views).get('data-value'))
        comment_count = str_to_int(self._search_regex(
            r'>All [Cc]omments? \(([\d,.]+)\)',
            webpage, 'comment count', default=None))

        def extract_tag_box(regex, title):
            tag_box = self._search_regex(regex, webpage, title, default=None)
            if not tag_box:
                return []
            return re.findall(r'<a[^>]+href=[^>]+>([^<]+)', tag_box)

        categories = extract_tag_box(
            r'(?s)Categories:.*?</[^>]+>(.+?)</div>', 'categories')
        tags = extract_tag_box(
            r'(?s)Tags:.*?</div>\s*<div[^>]+class=["\']tagBoxContent["\'][^>]*>(.+?)</div>',
            'tags')

        data = self._search_json_ld(webpage, video_id, expected_type='VideoObject', fatal=False) or {}
        data.pop('url', None)

        result = merge_dicts(data, {
            'id': video_id,
            'display_id': display_id if display_id != video_id else None,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'upload_date': upload_date,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
        })
        return result

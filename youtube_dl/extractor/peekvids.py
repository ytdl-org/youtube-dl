# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_class,
    int_or_none,
    merge_dicts,
    url_or_none,
)


class PeekVidsIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?peekvids\.com/
        (?:(?:[^/?#]+/){2}|embed/?\?(?:[^#]*&)?v=)
        (?P<id>[^/?&#]*)
    '''
    _TESTS = [{
        'url': 'https://peekvids.com/pc/dane-jones-cute-redhead-with-perfect-tits-with-mini-vamp/BSyLMbN0YCd',
        'md5': '2ff6a357a9717dc9dc9894b51307e9a2',
        'info_dict': {
            'id': '1262717',
            'display_id': 'BSyLMbN0YCd',
            'title': ' Dane Jones - Cute redhead with perfect tits with Mini Vamp',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:0a61df3620de26c0af8963b1a730cd69',
            'timestamp': 1642579329,
            'upload_date': '20220119',
            'duration': 416,
            'view_count': int,
            'age_limit': 18,
            'uploader': 'SEXYhub.com',
            'categories': list,
            'tags': list,
        },
    }]
    _DOMAIN = 'www.peekvids.com'

    def _get_detail(self, html):
        return get_element_by_class('detail-video-block', html)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, expected_status=429)
        if '>Rate Limit Exceeded' in webpage:
            raise ExtractorError(
                '[%s] %s: %s' % (self.IE_NAME, video_id, 'You are suspected as a bot. Wait, or pass the captcha test on the site and provide --cookies.'),
                expected=True)

        title = self._html_search_regex(r'(?s)<h1\b[^>]*>(.+?)</h1>', webpage, 'title')

        display_id = video_id
        video_id = self._search_regex(r'(?s)<video\b[^>]+\bdata-id\s*=\s*["\']?([\w-]+)', webpage, 'short video ID')
        srcs = self._download_json(
            'https://%s/v-alt/%s' % (self._DOMAIN, video_id), video_id,
            note='Downloading list of source files')
        formats = [{
            'url': f_url,
            'format_id': f_id,
            'height': int_or_none(f_id),
        } for f_url, f_id in (
            (url_or_none(f_v), f_match.group(1))
            for f_v, f_match in (
                (v, re.match(r'^data-src(\d{3,})$', k))
                for k, v in srcs.items() if v) if f_match)
            if f_url
        ]
        if not formats:
            formats = [{'url': url} for url in srcs.values()]
        self._sort_formats(formats)

        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        # may not have found the thumbnail if it was in a list in the ld+json
        info.setdefault('thumbnail', self._og_search_thumbnail(webpage))
        detail = self._get_detail(webpage) or ''
        info['description'] = self._html_search_regex(
            r'(?s)(.+?)(?:%s\s*<|<ul\b)' % (re.escape(info.get('description', '')), ),
            detail, 'description', default=None) or None
        info['title'] = re.sub(r'\s*[,-][^,-]+$', '', info.get('title') or title) or self._generic_title(url)

        def cat_tags(name, html):
            l = self._html_search_regex(
                r'(?s)<span\b[^>]*>\s*%s\s*:\s*</span>(.+?)</li>' % (re.escape(name), ),
                html, name, default='')
            return [x for x in re.split(r'\s+', l) if x]

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'age_limit': 18,
            'formats': formats,
            'categories': cat_tags('Categories', detail),
            'tags': cat_tags('Tags', detail),
            'uploader': self._html_search_regex(r'[Uu]ploaded\s+by\s(.+?)"', webpage, 'uploader', default=None),
        }, info)


class PlayVidsIE(PeekVidsIE):
    _VALID_URL = r'https?://(?:www\.)?playvids\.com/(?:embed/|\w\w?/)?(?P<id>[^/?#]*)'
    _TESTS = [{
        'url': 'https://www.playvids.com/U3pBrYhsjXM/pc/dane-jones-cute-redhead-with-perfect-tits-with-mini-vamp',
        'md5': '2f12e50213dd65f142175da633c4564c',
        'info_dict': {
            'id': '1978030',
            'display_id': 'U3pBrYhsjXM',
            'title': ' Dane Jones - Cute redhead with perfect tits with Mini Vamp',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:0a61df3620de26c0af8963b1a730cd69',
            'timestamp': 1640435839,
            'upload_date': '20211225',
            'duration': 416,
            'view_count': int,
            'age_limit': 18,
            'uploader': 'SEXYhub.com',
            'categories': list,
            'tags': list,
        },
    }, {
        'url': 'https://www.playvids.com/es/U3pBrYhsjXM/pc/dane-jones-cute-redhead-with-perfect-tits-with-mini-vamp',
        'only_matching': True,
    }, {
        'url': 'https://www.playvids.com/embed/U3pBrYhsjXM',
        'only_matching': True,
    }, {
        'url': 'https://www.playvids.com/bKmGLe3IwjZ/sv/brazzers-800-phone-sex-madison-ivy-always-on-the-line',
        'md5': 'e783986e596cafbf46411a174ab42ba6',
        'info_dict': {
            'id': '762385',
            'display_id': 'bKmGLe3IwjZ',
            'ext': 'mp4',
            'title': 'Brazzers - 1 800 Phone Sex: Madison Ivy Always On The Line 6',
            'description': 'md5:bdcd2db2b8ad85831a491d7c8605dcef',
            'timestamp': 1516958544,
            'upload_date': '20180126',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 480,
            'uploader': 'Brazzers',
            'age_limit': 18,
            'view_count': int,
            'age_limit': 18,
            'categories': list,
            'tags': list,
        },
    }, {
        'url': 'https://www.playvids.com/v/47iUho33toY',
        'md5': 'b056b5049d34b648c1e86497cf4febce',
        'info_dict': {
            'id': '700621',
            'display_id': '47iUho33toY',
            'ext': 'mp4',
            'title': 'KATEE OWEN STRIPTIASE IN SEXY RED LINGERIE',
            'description': None,
            'timestamp': 1507052209,
            'upload_date': '20171003',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 332,
            'uploader': 'Cacerenele',
            'age_limit': 18,
            'view_count': int,
            'categories': list,
            'tags': list,
        }
    }, {
        'url': 'https://www.playvids.com/z3_7iwWCmqt/sexy-teen-filipina-striptease-beautiful-pinay-bargirl-strips-and-dances',
        'md5': 'efa09be9f031314b7b7e3bc6510cd0df',
        'info_dict': {
            'id': '1523518',
            'display_id': 'z3_7iwWCmqt',
            'ext': 'mp4',
            'title': 'SEXY TEEN FILIPINA STRIPTEASE - Beautiful Pinay Bargirl Strips and Dances',
            'description': None,
            'timestamp': 1607470323,
            'upload_date': '20201208',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 593,
            'uploader': 'yorours',
            'age_limit': 18,
            'view_count': int,
            'categories': list,
            'tags': list,
        },
    }]
    _DOMAIN = 'www.playvids.com'

    def _get_detail(self, html):
        return get_element_by_class('detail-block', html)

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    merge_dicts,
    str_or_none,
    T,
    traverse_obj,
    url_or_none,
)


class WhypIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?whyp\.it/tracks/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.whyp.it/tracks/18337/home-page-example-track-b4kq7',
        'md5': 'c1187b42ebf8605284e3dc92aeb33d16',
        'info_dict': {
            'url': 'https://cdn.whyp.it/50eb17cc-e9ff-4e18-b89b-dc9206a95cb1.mp3',
            'id': '18337',
            'title': 'Home Page Example Track',
            'description': 'md5:bd758000fb93f3159339c852b5b9133c',
            'ext': 'mp3',
            'duration': 52.82,
            'uploader': 'Brad',
            'uploader_id': '1',
            'thumbnail': 'https://cdn.whyp.it/a537bb36-3373-4c61-96c8-27fc1b2f427a.jpg',
        },
    }, {
        'url': 'https://www.whyp.it/tracks/18337',
        'only_matching': True,
    }]

    def _search_nuxt_data(self, webpage, video_id, context_name='__NUXT__', fatal=True, traverse=('data', 0)):
        """Parses Nuxt.js metadata. This works as long as the function __NUXT__ invokes is a pure function"""

        import functools
        import json
        import re
        from ..utils import (js_to_json, NO_DEFAULT)

        re_ctx = re.escape(context_name)
        FUNCTION_RE = r'\(function\((?P<arg_keys>.*?)\){return\s+(?P<js>{.*?})\s*;?\s*}\((?P<arg_vals>.*?)\)'
        js, arg_keys, arg_vals = self._search_regex(
            (p.format(re_ctx, FUNCTION_RE) for p in (r'<script>\s*window\.{0}={1}\s*\)\s*;?\s*</script>', r'{0}\(.*?{1}')),
            webpage, context_name, group=('js', 'arg_keys', 'arg_vals'),
            default=NO_DEFAULT if fatal else (None, None, None))
        if js is None:
            return {}

        args = dict(zip(arg_keys.split(','), map(json.dumps, self._parse_json(
            '[{0}]'.format(arg_vals), video_id, transform_source=js_to_json, fatal=fatal) or ())))

        ret = self._parse_json(js, video_id, transform_source=functools.partial(js_to_json, vars=args), fatal=fatal)
        return traverse_obj(ret, traverse) or {}

    def _real_extract(self, url):
        unique_id = self._match_id(url)
        webpage = self._download_webpage(url, unique_id)
        data = self._search_nuxt_data(webpage, unique_id)['rawTrack']

        return merge_dicts({
            'url': data['audio_url'],
            'id': unique_id,
        }, traverse_obj(data, {
            'title': 'title',
            'description': 'description',
            'duration': ('duration', T(float_or_none)),
            'uploader': ('user', 'username'),
            'uploader_id': ('user', 'id', T(str_or_none)),
            'thumbnail': ('artwork_url', T(url_or_none)),
        }), {
            'ext': 'mp3',
            'vcodec': 'none',
            'http_headers': {'Referer': 'https://whyp.it/'},
        }, rev=True)

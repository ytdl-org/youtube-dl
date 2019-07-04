# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    js_to_json,
    parse_iso8601,
)


class NetzkinoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?netzkino\.de/\#!/(?P<category>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.netzkino.de/#!/scifikino/rakete-zum-mond',
        'md5': '92a3f8b76f8d7220acce5377ea5d4873',
        'info_dict': {
            'id': 'rakete-zum-mond',
            'ext': 'mp4',
            'title': 'Rakete zum Mond (Endstation Mond, Destination Moon)',
            'comments': 'mincount:3',
            'description': 'md5:1eddeacc7e62d5a25a2d1a7290c64a28',
            'upload_date': '20120813',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1344858571,
            'age_limit': 12,
        },
        'params': {
            'skip_download': 'Download only works from Germany',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        category_id = mobj.group('category')
        video_id = mobj.group('id')

        api_url = 'http://api.netzkino.de.simplecache.net/capi-2.0a/categories/%s.json?d=www' % category_id
        api_info = self._download_json(api_url, video_id)
        info = next(
            p for p in api_info['posts'] if p['slug'] == video_id)
        custom_fields = info['custom_fields']

        production_js = self._download_webpage(
            'http://www.netzkino.de/beta/dist/production.min.js', video_id,
            note='Downloading player code')
        avo_js = self._search_regex(
            r'var urlTemplate=(\{.*?"\})',
            production_js, 'URL templates')
        templates = self._parse_json(
            avo_js, video_id, transform_source=js_to_json)

        suffix = {
            'hds': '.mp4/manifest.f4m',
            'hls': '.mp4/master.m3u8',
            'pmd': '.mp4',
        }
        film_fn = custom_fields['Streaming'][0]
        formats = [{
            'format_id': key,
            'ext': 'mp4',
            'url': tpl.replace('{}', film_fn) + suffix[key],
        } for key, tpl in templates.items()]
        self._sort_formats(formats)

        comments = [{
            'timestamp': parse_iso8601(c.get('date'), delimiter=' '),
            'id': c['id'],
            'author': c['name'],
            'html': c['content'],
            'parent': 'root' if c.get('parent', 0) == 0 else c['parent'],
        } for c in info.get('comments', [])]

        return {
            'id': video_id,
            'formats': formats,
            'comments': comments,
            'title': info['title'],
            'age_limit': int_or_none(custom_fields.get('FSK')[0]),
            'timestamp': parse_iso8601(info.get('date'), delimiter=' '),
            'description': clean_html(info.get('content')),
            'thumbnail': info.get('thumbnail'),
            'playlist_title': api_info.get('title'),
            'playlist_id': category_id,
        }

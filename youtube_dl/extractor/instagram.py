from __future__ import unicode_literals

import itertools
import json
import os
import re
import subprocess
import tempfile

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    check_executable,
    ExtractorError,
    get_element_by_attribute,
    int_or_none,
    lowercase_escape,
    std_headers,
    try_get,
)


class InstagramIE(InfoExtractor):
    _VALID_URL = r'(?P<url>https?://(?:www\.)?instagram\.com/p/(?P<id>[^/?#&]+))'
    _TESTS = [{
        'url': 'https://instagram.com/p/aye83DjauH/?foo=bar#abc',
        'md5': '0d2da106a9d2631273e192b372806516',
        'info_dict': {
            'id': 'aye83DjauH',
            'ext': 'mp4',
            'title': 'Video by naomipq',
            'description': 'md5:1f17f0ab29bd6fe2bfad705f58de3cb8',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1371748545,
            'upload_date': '20130620',
            'uploader_id': 'naomipq',
            'uploader': 'Naomi Leonor Phan-Quang',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
    }, {
        # missing description
        'url': 'https://www.instagram.com/p/BA-pQFBG8HZ/?taken-by=britneyspears',
        'info_dict': {
            'id': 'BA-pQFBG8HZ',
            'ext': 'mp4',
            'title': 'Video by britneyspears',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1453760977,
            'upload_date': '20160125',
            'uploader_id': 'britneyspears',
            'uploader': 'Britney Spears',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # multi video post
        'url': 'https://www.instagram.com/p/BQ0eAlwhDrw/',
        'playlist': [{
            'info_dict': {
                'id': 'BQ0dSaohpPW',
                'ext': 'mp4',
                'title': 'Video 1',
            },
        }, {
            'info_dict': {
                'id': 'BQ0dTpOhuHT',
                'ext': 'mp4',
                'title': 'Video 2',
            },
        }, {
            'info_dict': {
                'id': 'BQ0dT7RBFeF',
                'ext': 'mp4',
                'title': 'Video 3',
            },
        }],
        'info_dict': {
            'id': 'BQ0eAlwhDrw',
            'title': 'Post by instagram',
            'description': 'md5:0f9203fc6a2ce4d228da5754bcf54957',
        },
    }, {
        'url': 'https://instagram.com/p/-Cmh1cukG2/',
        'only_matching': True,
    }, {
        'url': 'http://instagram.com/p/9o6LshA7zy/embed/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_embed_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?instagram\.com/p/[^/]+/embed.*?)\1',
            webpage)
        if mobj:
            return mobj.group('url')

        blockquote_el = get_element_by_attribute(
            'class', 'instagram-media', webpage)
        if blockquote_el is None:
            return

        mobj = re.search(
            r'<a[^>]+href=([\'"])(?P<link>[^\'"]+)\1', blockquote_el)
        if mobj:
            return mobj.group('link')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = mobj.group('url')

        webpage = self._download_webpage(url, video_id)

        (video_url, description, thumbnail, timestamp, uploader,
         uploader_id, like_count, comment_count, comments, height,
         width) = [None] * 11

        shared_data = self._parse_json(
            self._search_regex(
                r'window\._sharedData\s*=\s*({.+?});',
                webpage, 'shared data', default='{}'),
            video_id, fatal=False)
        if shared_data:
            media = try_get(
                shared_data,
                (lambda x: x['entry_data']['PostPage'][0]['graphql']['shortcode_media'],
                 lambda x: x['entry_data']['PostPage'][0]['media']),
                dict)
            if media:
                video_url = media.get('video_url')
                height = int_or_none(media.get('dimensions', {}).get('height'))
                width = int_or_none(media.get('dimensions', {}).get('width'))
                description = try_get(
                    media, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                    compat_str) or media.get('caption')
                thumbnail = media.get('display_src')
                timestamp = int_or_none(media.get('taken_at_timestamp') or media.get('date'))
                uploader = media.get('owner', {}).get('full_name')
                uploader_id = media.get('owner', {}).get('username')

                def get_count(key, kind):
                    return int_or_none(try_get(
                        media, (lambda x: x['edge_media_%s' % key]['count'],
                                lambda x: x['%ss' % kind]['count'])))
                like_count = get_count('preview_like', 'like')
                comment_count = get_count('to_comment', 'comment')

                comments = [{
                    'author': comment.get('user', {}).get('username'),
                    'author_id': comment.get('user', {}).get('id'),
                    'id': comment.get('id'),
                    'text': comment.get('text'),
                    'timestamp': int_or_none(comment.get('created_at')),
                } for comment in media.get(
                    'comments', {}).get('nodes', []) if comment.get('text')]
                if not video_url:
                    edges = try_get(
                        media, lambda x: x['edge_sidecar_to_children']['edges'],
                        list) or []
                    if edges:
                        entries = []
                        for edge_num, edge in enumerate(edges, start=1):
                            node = try_get(edge, lambda x: x['node'], dict)
                            if not node:
                                continue
                            node_video_url = try_get(node, lambda x: x['video_url'], compat_str)
                            if not node_video_url:
                                continue
                            entries.append({
                                'id': node.get('shortcode') or node['id'],
                                'title': 'Video %d' % edge_num,
                                'url': node_video_url,
                                'thumbnail': node.get('display_url'),
                                'width': int_or_none(try_get(node, lambda x: x['dimensions']['width'])),
                                'height': int_or_none(try_get(node, lambda x: x['dimensions']['height'])),
                                'view_count': int_or_none(node.get('video_view_count')),
                            })
                        return self.playlist_result(
                            entries, video_id,
                            'Post by %s' % uploader_id if uploader_id else None,
                            description)

        if not video_url:
            video_url = self._og_search_video_url(webpage, secure=False)

        formats = [{
            'url': video_url,
            'width': width,
            'height': height,
        }]

        if not uploader_id:
            uploader_id = self._search_regex(
                r'"owner"\s*:\s*{\s*"username"\s*:\s*"(.+?)"',
                webpage, 'uploader id', fatal=False)

        if not description:
            description = self._search_regex(
                r'"caption"\s*:\s*"(.+?)"', webpage, 'description', default=None)
            if description is not None:
                description = lowercase_escape(description)

        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'formats': formats,
            'ext': 'mp4',
            'title': 'Video by %s' % uploader_id,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'uploader': uploader,
            'like_count': like_count,
            'comment_count': comment_count,
            'comments': comments,
        }


class InstagramUserIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/(?P<id>[^/]{2,})/?(?:$|[?#])'
    IE_DESC = 'Instagram user profile'
    IE_NAME = 'instagram:user'
    _TEST = {
        'url': 'https://instagram.com/porsche',
        'info_dict': {
            'id': 'porsche',
            'title': 'porsche',
        },
        'playlist_count': 5,
        'params': {
            'extract_flat': True,
            'skip_download': True,
            'playlistend': 5,
        }
    }

    _SIGN_CODE = '''
"use strict";
function i(e, t) {
    var r = (65535 & e) + (65535 & t);
    return (e >> 16) + (t >> 16) + (r >> 16) << 16 | 65535 & r
}
function a(e, t, r, n, o, a) {
    return i((s = i(i(t, e), i(n, a))) << (c = o) | s >>> 32 - c, r);
    var s, c
}
function s(e, t, r, n, o, i, s) {
    return a(t & r | ~t & n, e, t, o, i, s)
}
function c(e, t, r, n, o, i, s) {
    return a(t & n | r & ~n, e, t, o, i, s)
}
function u(e, t, r, n, o, i, s) {
    return a(t ^ r ^ n, e, t, o, i, s)
}
function l(e, t, r, n, o, i, s) {
    return a(r ^ (t | ~n), e, t, o, i, s)
}
function p(e, t) {
    var r, n, o, a, p;
    e[t >> 5] |= 128 << t % 32,
    e[14 + (t + 64 >>> 9 << 4)] = t;
    var d = 1732584193
      , f = -271733879
      , h = -1732584194
      , g = 271733878;
    for (r = 0; r < e.length; r += 16)
        n = d,
        o = f,
        a = h,
        p = g,
        f = l(f = l(f = l(f = l(f = u(f = u(f = u(f = u(f = c(f = c(f = c(f = c(f = s(f = s(f = s(f = s(f, h = s(h, g = s(g, d = s(d, f, h, g, e[r], 7, -680876936), f, h, e[r + 1], 12, -389564586), d, f, e[r + 2], 17, 606105819), g, d, e[r + 3], 22, -1044525330), h = s(h, g = s(g, d = s(d, f, h, g, e[r + 4], 7, -176418897), f, h, e[r + 5], 12, 1200080426), d, f, e[r + 6], 17, -1473231341), g, d, e[r + 7], 22, -45705983), h = s(h, g = s(g, d = s(d, f, h, g, e[r + 8], 7, 1770035416), f, h, e[r + 9], 12, -1958414417), d, f, e[r + 10], 17, -42063), g, d, e[r + 11], 22, -1990404162), h = s(h, g = s(g, d = s(d, f, h, g, e[r + 12], 7, 1804603682), f, h, e[r + 13], 12, -40341101), d, f, e[r + 14], 17, -1502002290), g, d, e[r + 15], 22, 1236535329), h = c(h, g = c(g, d = c(d, f, h, g, e[r + 1], 5, -165796510), f, h, e[r + 6], 9, -1069501632), d, f, e[r + 11], 14, 643717713), g, d, e[r], 20, -373897302), h = c(h, g = c(g, d = c(d, f, h, g, e[r + 5], 5, -701558691), f, h, e[r + 10], 9, 38016083), d, f, e[r + 15], 14, -660478335), g, d, e[r + 4], 20, -405537848), h = c(h, g = c(g, d = c(d, f, h, g, e[r + 9], 5, 568446438), f, h, e[r + 14], 9, -1019803690), d, f, e[r + 3], 14, -187363961), g, d, e[r + 8], 20, 1163531501), h = c(h, g = c(g, d = c(d, f, h, g, e[r + 13], 5, -1444681467), f, h, e[r + 2], 9, -51403784), d, f, e[r + 7], 14, 1735328473), g, d, e[r + 12], 20, -1926607734), h = u(h, g = u(g, d = u(d, f, h, g, e[r + 5], 4, -378558), f, h, e[r + 8], 11, -2022574463), d, f, e[r + 11], 16, 1839030562), g, d, e[r + 14], 23, -35309556), h = u(h, g = u(g, d = u(d, f, h, g, e[r + 1], 4, -1530992060), f, h, e[r + 4], 11, 1272893353), d, f, e[r + 7], 16, -155497632), g, d, e[r + 10], 23, -1094730640), h = u(h, g = u(g, d = u(d, f, h, g, e[r + 13], 4, 681279174), f, h, e[r], 11, -358537222), d, f, e[r + 3], 16, -722521979), g, d, e[r + 6], 23, 76029189), h = u(h, g = u(g, d = u(d, f, h, g, e[r + 9], 4, -640364487), f, h, e[r + 12], 11, -421815835), d, f, e[r + 15], 16, 530742520), g, d, e[r + 2], 23, -995338651), h = l(h, g = l(g, d = l(d, f, h, g, e[r], 6, -198630844), f, h, e[r + 7], 10, 1126891415), d, f, e[r + 14], 15, -1416354905), g, d, e[r + 5], 21, -57434055), h = l(h, g = l(g, d = l(d, f, h, g, e[r + 12], 6, 1700485571), f, h, e[r + 3], 10, -1894986606), d, f, e[r + 10], 15, -1051523), g, d, e[r + 1], 21, -2054922799), h = l(h, g = l(g, d = l(d, f, h, g, e[r + 8], 6, 1873313359), f, h, e[r + 15], 10, -30611744), d, f, e[r + 6], 15, -1560198380), g, d, e[r + 13], 21, 1309151649), h = l(h, g = l(g, d = l(d, f, h, g, e[r + 4], 6, -145523070), f, h, e[r + 11], 10, -1120210379), d, f, e[r + 2], 15, 718787259), g, d, e[r + 9], 21, -343485551),
        d = i(d, n),
        f = i(f, o),
        h = i(h, a),
        g = i(g, p);
    return [d, f, h, g]
}
function d(e) {
    var t, r = "", n = 32 * e.length;
    for (t = 0; t < n; t += 8)
        r += String.fromCharCode(e[t >> 5] >>> t % 32 & 255);
    return r
}
function f(e) {
    var t, r = [];
    for (r[(e.length >> 2) - 1] = void 0,
    t = 0; t < r.length; t += 1)
        r[t] = 0;
    var n = 8 * e.length;
    for (t = 0; t < n; t += 8)
        r[t >> 5] |= (255 & e.charCodeAt(t / 8)) << t % 32;
    return r
}
function h(e) {
    var t, r, n = "";
    for (r = 0; r < e.length; r += 1)
        t = e.charCodeAt(r),
        n += "0123456789abcdef".charAt(t >>> 4 & 15) + "0123456789abcdef".charAt(15 & t);
    return n
}
function g(e) {
    return unescape(encodeURIComponent(e))
}
function b(e) {
    return function(e) {
        return d(p(f(e), 8 * e.length))
    }(g(e))
}
function m(e, t) {
    return function(e, t) {
        var r, n, o = f(e), i = [], a = [];
        for (i[15] = a[15] = void 0,
        o.length > 16 && (o = p(o, 8 * e.length)),
        r = 0; r < 16; r += 1)
            i[r] = 909522486 ^ o[r],
            a[r] = 1549556828 ^ o[r];
        return n = p(i.concat(f(t)), 512 + 8 * t.length),
        d(p(a.concat(n), 640))
    }(g(e), g(t))
}
function v(e, t, r) {
    return t ? r ? m(t, e) : h(m(t, e)) : r ? b(e) : h(b(e))
}
function sign(s) {
    return v(s);
}
'''

    def _entries(self, data):
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        uploader_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        self._set_cookie('instagram.com', 'ig_pr', '1')

        def sign(s):
            js_code = self._SIGN_CODE + "console.log(sign('%s')); phantom.exit();" % s
            with open(self._phantomjs_script.name, 'w') as f:
                f.write(js_code)
            p = subprocess.Popen(
                ['phantomjs', '--ssl-protocol=any', f.name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            gis, err = p.communicate()
            if p.returncode != 0:
                raise ExtractorError('Failed to sign request\n:' + err.decode('utf-8'))
            return gis.decode('utf-8').strip()

        cursor = ''
        for page_num in itertools.count(1):
            variables = json.dumps({
                'id': uploader_id,
                'first': 100,
                'after': cursor,
            })
            gis = sign(
                '%s:%s:%s:%s'
                % (rhx_gis, csrf_token, std_headers['User-Agent'], variables))
            media = self._download_json(
                'https://www.instagram.com/graphql/query/', uploader_id,
                'Downloading JSON page %d' % page_num, headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-Instagram-GIS': gis,
                }, query={
                    'query_hash': '472f257a40c653c64c666ce877d59d2b',
                    'variables': variables,
                })['data']['user']['edge_owner_to_timeline_media']

            edges = media.get('edges')
            if not edges or not isinstance(edges, list):
                break

            for edge in edges:
                node = edge.get('node')
                if not node or not isinstance(node, dict):
                    continue
                if node.get('__typename') != 'GraphVideo' and node.get('is_video') is not True:
                    continue
                video_id = node.get('shortcode')
                if not video_id:
                    continue

                info = self.url_result(
                    'https://instagram.com/p/%s/' % video_id,
                    ie=InstagramIE.ie_key(), video_id=video_id)

                description = try_get(
                    node, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                    compat_str)
                thumbnail = node.get('thumbnail_src') or node.get('display_src')
                timestamp = int_or_none(node.get('taken_at_timestamp'))

                comment_count = get_count('to_comment')
                like_count = get_count('preview_like')
                view_count = int_or_none(node.get('video_view_count'))

                info.update({
                    'description': description,
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'comment_count': comment_count,
                    'like_count': like_count,
                    'view_count': view_count,
                })

                yield info

            page_info = media.get('page_info')
            if not page_info or not isinstance(page_info, dict):
                break

            has_next_page = page_info.get('has_next_page')
            if not has_next_page:
                break

            cursor = page_info.get('end_cursor')
            if not cursor or not isinstance(cursor, compat_str):
                break

    def _real_initialize(self):
        if not check_executable('phantomjs', ['-v']):
            raise ExtractorError(
                'PhantomJS executable not found in PATH, download it from http://phantomjs.org',
                expected=True)
        self._phantomjs_script = tempfile.NamedTemporaryFile(delete=False)
        self._phantomjs_script.close()

    def __del__(self):
        os.unlink(self._phantomjs_script.name)

    def _real_extract(self, url):
        username = self._match_id(url)

        webpage = self._download_webpage(url, username)

        data = self._parse_json(
            self._search_regex(
                r'sharedData\s*=\s*({.+?})\s*;\s*[<\n]', webpage, 'data'),
            username)

        return self.playlist_result(
            self._entries(data), username, username)

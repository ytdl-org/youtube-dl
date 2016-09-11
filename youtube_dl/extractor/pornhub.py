# coding: utf-8
from __future__ import unicode_literals

import itertools
import os
import re

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urllib_parse_unquote,
    compat_urllib_parse_unquote_plus,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    orderedSet,
    sanitized_Request,
    str_to_int,
)
from ..aes import (
    aes_decrypt_text
)


class PornHubIE(InfoExtractor):
    IE_DESC = 'PornHub and Thumbzilla'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[a-z]+\.)?pornhub\.com/(?:view_video\.php\?viewkey=|embed/)|
                            (?:www\.)?thumbzilla\.com/video/
                        )
                        (?P<id>[0-9a-z]+)
                    '''
    _TESTS = [{
        'url': 'http://www.pornhub.com/view_video.php?viewkey=648719015',
        'md5': '1e19b41231a02eba417839222ac9d58e',
        'info_dict': {
            'id': '648719015',
            'ext': 'mp4',
            'title': 'Seductive Indian beauty strips down and fingers her pink pussy',
            'uploader': 'Babes',
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
            'uploader': 'cj397186295',
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
    }]

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?pornhub\.com/embed/\d+)\1', webpage)
        if mobj:
            return mobj.group('url')

    def _extract_count(self, pattern, webpage, name):
        return str_to_int(self._search_regex(
            pattern, webpage, '%s count' % name, fatal=False))

    def _real_extract(self, url):
        video_id = self._match_id(url)

        req = sanitized_Request(
            'http://www.pornhub.com/view_video.php?viewkey=%s' % video_id)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

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

        flashvars = self._parse_json(
            self._search_regex(
                r'var\s+flashvars_\d+\s*=\s*({.+?});', webpage, 'flashvars', default='{}'),
            video_id)
        if flashvars:
            thumbnail = flashvars.get('image_url')
            duration = int_or_none(flashvars.get('video_duration'))
        else:
            title, thumbnail, duration = [None] * 3

        video_uploader = self._html_search_regex(
            r'(?s)From:&nbsp;.+?<(?:a href="/users/|a href="/channels/|span class="username)[^>]+>(.+?)<',
            webpage, 'uploader', fatal=False)

        view_count = self._extract_count(
            r'<span class="count">([\d,\.]+)</span> views', webpage, 'view')
        like_count = self._extract_count(
            r'<span class="votesUp">([\d,\.]+)</span>', webpage, 'like')
        dislike_count = self._extract_count(
            r'<span class="votesDown">([\d,\.]+)</span>', webpage, 'dislike')
        comment_count = self._extract_count(
            r'All Comments\s*<span>\(([\d,.]+)\)', webpage, 'comment')

        video_urls = list(map(compat_urllib_parse_unquote, re.findall(r"player_quality_[0-9]{3}p\s*=\s*'([^']+)'", webpage)))
        if webpage.find('"encrypted":true') != -1:
            password = compat_urllib_parse_unquote_plus(
                self._search_regex(r'"video_title":"([^"]+)', webpage, 'password'))
            video_urls = list(map(lambda s: aes_decrypt_text(s, password, 32).decode('utf-8'), video_urls))

        formats = []
        for video_url in video_urls:
            path = compat_urllib_parse_urlparse(video_url).path
            extension = os.path.splitext(path)[1][1:]
            format = path.split('/')[5].split('_')[:2]
            format = '-'.join(format)

            m = re.match(r'^(?P<height>[0-9]+)[pP]-(?P<tbr>[0-9]+)[kK]$', format)
            if m is None:
                height = None
                tbr = None
            else:
                height = int(m.group('height'))
                tbr = int(m.group('tbr'))

            formats.append({
                'url': video_url,
                'ext': extension,
                'format': format,
                'format_id': format,
                'tbr': tbr,
                'height': height,
            })
        self._sort_formats(formats)

        page_params = self._parse_json(self._search_regex(
            r'page_params\.zoneDetails\[([\'"])[^\'"]+\1\]\s*=\s*(?P<data>{[^}]+})',
            webpage, 'page parameters', group='data', default='{}'),
            video_id, transform_source=js_to_json, fatal=False)
        tags = categories = None
        if page_params:
            tags = page_params.get('tags', '').split(',')
            categories = page_params.get('categories', '').split(',')

        return {
            'id': video_id,
            'uploader': video_uploader,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
            'tags': tags,
            'categories': categories,
        }


class PornHubPlaylistBaseIE(InfoExtractor):
    def _extract_entries(self, webpage):
        return [
            self.url_result(
                'http://www.pornhub.com/%s' % video_url,
                PornHubIE.ie_key(), video_title=title)
            for video_url, title in orderedSet(re.findall(
                r'href="/?(view_video\.php\?.*\bviewkey=[\da-z]+[^"]*)"[^>]*\s+title="([^"]+)"',
                webpage))
        ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = self._extract_entries(webpage)

        playlist = self._parse_json(
            self._search_regex(
                r'playlistObject\s*=\s*({.+?});', webpage, 'playlist'),
            playlist_id)

        return self.playlist_result(
            entries, playlist_id, playlist.get('title'), playlist.get('description'))


class PornHubPlaylistIE(PornHubPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?pornhub\.com/playlist/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.pornhub.com/playlist/6201671',
        'info_dict': {
            'id': '6201671',
            'title': 'P0p4',
        },
        'playlist_mincount': 35,
    }]


class PornHubUserVideosIE(PornHubPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?pornhub\.com/users/(?P<id>[^/]+)/videos'
    _TESTS = [{
        'url': 'http://www.pornhub.com/users/zoe_ph/videos/public',
        'info_dict': {
            'id': 'zoe_ph',
        },
        'playlist_mincount': 171,
    }, {
        'url': 'http://www.pornhub.com/users/rushandlia/videos',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        user_id = self._match_id(url)

        entries = []
        for page_num in itertools.count(1):
            try:
                webpage = self._download_webpage(
                    url, user_id, 'Downloading page %d' % page_num,
                    query={'page': page_num})
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                    break
            page_entries = self._extract_entries(webpage)
            if not page_entries:
                break
            entries.extend(page_entries)

        return self.playlist_result(entries, user_id)

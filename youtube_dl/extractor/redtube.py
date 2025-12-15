# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    join_nonempty,
    merge_dicts,
    str_to_int,
    T,
    traverse_obj,
    unified_strdate,
    url_or_none,
    urljoin,
)


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:\w+\.)?redtube\.com/|embed\.redtube\.com/\?.*?\bid=)(?P<id>[0-9]+)'
    _EMBED_REGEX = [r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//embed\.redtube\.com/\?.*?\bid=\d+)']
    _TESTS = [{
        'url': 'https://www.redtube.com/38864951',
        'md5': 'd7de9cb32e8adb3f6379f1a30f655fae',
        'info_dict': {
            'id': '38864951',
            'ext': 'mp4',
            'title': 'Public Sex on the Balcony in Freezing Paris! Amateur Couple LeoLulu',
            'description': 'Watch video Public Sex on the Balcony in Freezing Paris! Amateur Couple LeoLulu on Redtube, home of free Blowjob porn videos and Blonde sex movies online. Video length: (10:46) - Uploaded by leolulu - Verified User - Starring Pornstar: LeoLulu',
            'upload_date': '20210111',
            'timestamp': 1610343109,
            'duration': 646,
            'view_count': int,
            'age_limit': 18,
            'thumbnail': r're:https://\wi-ph\.rdtcdn\.com/videos/.+/.+\.jpg',
        },
        'expected_warnings': [
            'Failed to download m3u8 information: HTTP Error 404',
        ],
        'params': {
            'format': '[format_id !^= hls]',
        },
    }, {
        'url': 'http://embed.redtube.com/?bgcolor=000000&id=1443286',
        'only_matching': True,
    }, {
        'url': 'http://it.redtube.com/66418',
        'only_matching': True,
    }]

    @classmethod
    def _extract_urls(cls, webpage):
        for embed_re in cls._EMBED_REGEX:
            for from_ in re.findall(embed_re, webpage):
                yield from_

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://www.redtube.com/%s' % video_id, video_id)

        ERRORS = (
            (('video-deleted-info', '>This video has been removed'), 'has been removed'),
            (('private_video_text', '>This video is private', '>Send a friend request to its owner to be able to view it'), 'is private'),
        )

        for patterns, message in ERRORS:
            if any(p in webpage for p in patterns):
                raise ExtractorError(
                    'Video %s %s' % (video_id, message), expected=True)

        info = self._search_json_ld(webpage, video_id, default={})

        if not info.get('title'):
            info['title'] = self._html_search_regex(
                (r'<h(\d)[^>]+class="(?:video_title_text|videoTitle|video_title)[^"]*">(?P<title>(?:(?!\1).)+)</h\1>',
                 r'(?:videoTitle|title)\s*:\s*(["\'])(?P<title>(?:(?!\1).)+)\1',),
                webpage, 'title', group='title',
                default=None) or self._og_search_title(webpage)

        formats = []
        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})', webpage, 'source', default='{}'),
            video_id, fatal=False)

        def full_url(u):
            return urljoin(url, u)

        for fmt in traverse_obj(sources, (T(dict.items), {
                'url': (1, T(full_url)),
                'format_id': (2, T(compat_str)),
                'height': (2, T(int_or_none)), })):
            if 'url' in fmt:
                formats.append(fmt)

        medias = self._search_regex(
            r'''mediaDefinitions?["']?\s*:\s*(\[[\s\S]+?}\s*\])''', webpage,
            'media definitions', default='{}')
        medias = self._parse_json(medias, video_id, fatal=False)
        for fmt in traverse_obj(medias, (Ellipsis, T(dict))):
            format_url = full_url(fmt.get('videoUrl'))
            if not format_url:
                continue
            more_media = None
            if fmt['format'] == 'hls' or (fmt['format'] == 'mp4' and not fmt.get('quality')):
                more_media = self._download_json(format_url, video_id, fatal=False)
            if more_media is None:
                more_media = [fmt]
            for fmt in traverse_obj(more_media, (Ellipsis, {
                    'url': ('videoUrl', T(full_url)),
                    'ext': ('format', T(compat_str)),
                    'format_id': ('quality', T(compat_str)), })):
                format_url = fmt.get('url')
                if not format_url:
                    continue
                if fmt.get('ext') == 'hls' or determine_ext(format_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                    continue
                fmt['height'] = int_or_none(fmt.get('format_id'))
                fmt['format_id'] = join_nonempty('ext', 'format_id', from_dict=fmt)
                formats.append(fmt)
        if not formats:
            video_url = url_or_none(self._html_search_regex(
                r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL'))
            if video_url:
                formats.append({'url': video_url})

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        upload_date = unified_strdate(self._search_regex(
            r'<span[^>]+>(?:ADDED|Published on) ([^<]+)<',
            webpage, 'upload date', default=None))
        duration = int_or_none(self._og_search_property(
            'video:duration', webpage, default=None) or self._search_regex(
                r'videoDuration\s*:\s*(\d+)', webpage, 'duration', default=None))
        view_count = str_to_int(self._search_regex(
            (r'<div[^>]*>Views</div>\s*<div[^>]*>\s*([\d,.]+)',
             r'<span[^>]*>VIEWS</span>\s*</td>\s*<td>\s*([\d,.]+)',
             r'<span[^>]+\bclass=["\']video_view_count[^>]*>\s*([\d,.]+)'),
            webpage, 'view count', default=None))

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return merge_dicts(info, {
            'id': video_id,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        })

from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    merge_dicts,
    str_to_int,
    unified_strdate,
    url_or_none,
)


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:\w+\.)?redtube\.com/|embed\.redtube\.com/\?.*?\bid=)(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.redtube.com/66418',
        'md5': 'fc08071233725f26b8f014dba9590005',
        'info_dict': {
            'id': '66418',
            'ext': 'mp4',
            'title': 'Sucked on a toilet',
            'upload_date': '20110811',
            'duration': 596,
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'http://embed.redtube.com/?bgcolor=000000&id=1443286',
        'only_matching': True,
    }, {
        'url': 'http://it.redtube.com/66418',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//embed\.redtube\.com/\?.*?\bid=\d+)',
            webpage)

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

        formats = self._get_formats(webpage, video_id)

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

    def _get_formats(self, webpage, video_id):
        formats = []

        matches = re.findall(r'\{.+?\}', webpage)
        if matches is not None:
            for match in matches:
                try:
                    match = json.loads(match)
                    if 'videoUrl' in match:
                        url = match['videoUrl']
                        if url.startswith('https://www.redtube.com/media/mp4?'):
                            self._add_formats(formats, url, 'mp4', video_id)
                        elif url.startswith('https://www.redtube.com/media/hls?'):
                            self._add_formats(formats, url, 'hls', video_id)
                except json.decoder.JSONDecodeError as e:
                    pass  # print(e)

        self._sort_formats(formats)
        return formats

    def _add_formats(self, formats, url, codec, video_id):
        raw_meta = self._download_webpage(url, video_id)
        meta = json.loads(raw_meta)

        for stream in meta:
            quality = stream['quality']
            if isinstance(quality, list):
                quality = quality[0]

            format = {
                'url': stream['videoUrl'],
                'format_id': '%s-%s' % (quality, codec),
                'height': int(quality),
            }

            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', format['url'])
            if mobj:
                height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                format.update({
                    'height': height,
                    'tbr': bitrate,
                })

            formats.append(format)

        return formats

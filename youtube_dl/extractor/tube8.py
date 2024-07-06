from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    traverse_obj,
    T,
    url_or_none,
    parse_iso8601,
)


class Tube8IE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?tube8\.com\/+[^\/]+\/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tube8.com/porn-video/189530841/',
        'md5': '532408f59e89a32027d873af6289c85a',
        'info_dict': {
            'id': '189530841',
            'ext': 'mp4',
            'title': 'Found dildo. She let it cum in her tight ass to keep the secret',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'MaryKrylova',
            'timestamp': 1718961736,
            'upload_date': '20240621',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_valid_url(url).group('id')
        webpage = self._download_webpage(url, video_id)

        playervars = self._search_json(
            r'\bplayervars\s*:', webpage, 'playervars', video_id)

        extra_info = self._search_json(
            r'application/ld\+json[\"\']?>\s?', webpage, 'extra_info', video_id)

        uploader = traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('author'), 'author'))[0]

        thumbnail = traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('thumbnail'), 'thumbnail'))[0]

        timestamp = parse_iso8601(traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('datePublished'), 'datePublished'))[0])

        # Borrowed from youporn extractor
        def get_fmt(x):
            v_url = url_or_none(x.get('videoUrl'))
            if v_url:
                x['videoUrl'] = v_url
                return (x['format'], x)

        defs_by_format = dict(traverse_obj(playervars, (
            'mediaDefinitions', lambda _, v: v.get('format'), T(get_fmt))))

        title = traverse_obj(playervars, 'video_title')
        if not thumbnail:
            thumbnail = traverse_obj(playervars, 'image_url')

        # Borrowed from youporn extractor
        def get_format_data(f):
            if f not in defs_by_format:
                return []
            return self._download_json(
                defs_by_format[f]['videoUrl'], video_id, '{0}-formats'.format(f))

        formats = []
        for mp4_url in traverse_obj(
                get_format_data('mp4'),
                (lambda _, v: not isinstance(v['defaultQuality'], bool), 'videoUrl'),
                (Ellipsis, 'videoUrl')):
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', mp4_url)
            if mobj:
                height = int(mobj.group('height'))
                tbr = int(mobj.group('bitrate'))
                formats.append({
                    'format_id': '%dp-%dk' % (height, tbr),
                    'url': mp4_url,
                    'ext': 'mp4',
                    'tbr': tbr,
                    'height': height,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'uploader': uploader,
            'timestamp': timestamp,
        }

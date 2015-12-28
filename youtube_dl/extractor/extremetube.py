from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    sanitized_Request,
    str_to_int,
)


class ExtremeTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?extremetube\.com/(?:[^/]+/)?video/(?P<id>[^/#?&]+)'
    _TESTS = [{
        'url': 'http://www.extremetube.com/video/music-video-14-british-euro-brit-european-cumshots-swallow-652431',
        'md5': '344d0c6d50e2f16b06e49ca011d8ac69',
        'info_dict': {
            'id': 'music-video-14-british-euro-brit-european-cumshots-swallow-652431',
            'ext': 'mp4',
            'title': 'Music Video 14 british euro brit european cumshots swallow',
            'uploader': 'unknown',
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'http://www.extremetube.com/gay/video/abcde-1234',
        'only_matching': True,
    }, {
        'url': 'http://www.extremetube.com/video/latina-slut-fucked-by-fat-black-dick',
        'only_matching': True,
    }, {
        'url': 'http://www.extremetube.com/video/652431',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        req = sanitized_Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(
            r'<h1 [^>]*?title="([^"]+)"[^>]*>', webpage, 'title')
        uploader = self._html_search_regex(
            r'Uploaded by:\s*</strong>\s*(.+?)\s*</div>',
            webpage, 'uploader', fatal=False)
        view_count = str_to_int(self._html_search_regex(
            r'Views:\s*</strong>\s*<span>([\d,\.]+)</span>',
            webpage, 'view count', fatal=False))

        flash_vars = self._parse_json(
            self._search_regex(
                r'var\s+flashvars\s*=\s*({.+?});', webpage, 'flash vars'),
            video_id)

        formats = []
        for quality_key, video_url in flash_vars.items():
            height = int_or_none(self._search_regex(
                r'quality_(\d+)[pP]$', quality_key, 'height', default=None))
            if not height:
                continue
            f = {
                'url': video_url,
            }
            mobj = re.search(
                r'/(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', video_url)
            if mobj:
                height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                f.update({
                    'format_id': '%dp-%dk' % (height, bitrate),
                    'height': height,
                    'tbr': bitrate,
                })
            else:
                f.update({
                    'format_id': '%dp' % height,
                    'height': height,
                })
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'uploader': uploader,
            'view_count': view_count,
            'age_limit': 18,
        }

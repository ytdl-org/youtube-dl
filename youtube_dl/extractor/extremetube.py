from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_request,
)
from ..utils import (
    qualities,
    str_to_int,
)


class ExtremeTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>extremetube\.com/.*?video/.+?(?P<id>[0-9]+))(?:[/?&]|$)'
    _TESTS = [{
        'url': 'http://www.extremetube.com/video/music-video-14-british-euro-brit-european-cumshots-swallow-652431',
        'md5': '344d0c6d50e2f16b06e49ca011d8ac69',
        'info_dict': {
            'id': '652431',
            'ext': 'mp4',
            'title': 'Music Video 14 british euro brit european cumshots swallow',
            'uploader': 'unknown',
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'http://www.extremetube.com/gay/video/abcde-1234',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
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

        flash_vars = compat_parse_qs(self._search_regex(
            r'<param[^>]+?name="flashvars"[^>]+?value="([^"]+)"', webpage, 'flash vars'))

        formats = []
        quality = qualities(['180p', '240p', '360p', '480p', '720p', '1080p'])
        for k, vals in flash_vars.items():
            m = re.match(r'quality_(?P<quality>[0-9]+p)$', k)
            if m is not None:
                formats.append({
                    'format_id': m.group('quality'),
                    'quality': quality(m.group('quality')),
                    'url': vals[0],
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'uploader': uploader,
            'view_count': view_count,
            'age_limit': 18,
        }

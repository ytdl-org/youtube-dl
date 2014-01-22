from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
)
from ..aes import (
    aes_decrypt_text
)


class SpankwireIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>spankwire\.com/[^/]*/video(?P<videoid>[0-9]+)/?)'
    _TEST = {
        'url': 'http://www.spankwire.com/Buckcherry-s-X-Rated-Music-Video-Crazy-Bitch/video103545/',
        'file': '103545.mp4',
        'md5': '1b3f55e345500552dbc252a3e9c1af43',
        'info_dict': {
            "uploader": "oreusz",
            "title": "Buckcherry`s X Rated Music Video Crazy Bitch",
            "description": "Crazy Bitch X rated music video.",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<h1>([^<]+)', webpage, 'title')
        video_uploader = self._html_search_regex(
            r'by:\s*<a [^>]*>(.+?)</a>', webpage, 'uploader', fatal=False)
        thumbnail = self._html_search_regex(
            r'flashvars\.image_url = "([^"]+)', webpage, 'thumbnail', fatal=False)
        description = self._html_search_regex(
            r'<div\s+id="descriptionContent">([^<]+)<', webpage, 'description', fatal=False)

        video_urls = list(map(compat_urllib_parse.unquote , re.findall(r'flashvars\.quality_[0-9]{3}p = "([^"]+)', webpage)))
        if webpage.find('flashvars\.encrypted = "true"') != -1:
            password = self._html_search_regex(r'flashvars\.video_title = "([^"]+)', webpage, 'password').replace('+', ' ')
            video_urls = list(map(lambda s: aes_decrypt_text(s, password, 32).decode('utf-8'), video_urls))

        formats = []
        for video_url in video_urls:
            path = compat_urllib_parse_urlparse(video_url).path
            extension = os.path.splitext(path)[1][1:]
            format = path.split('/')[4].split('_')[:2]
            resolution, bitrate_str = format
            format = "-".join(format)
            height = int(resolution.rstrip('P'))
            tbr = int(bitrate_str.rstrip('K'))

            formats.append({
                'url': video_url,
                'ext': extension,
                'resolution': resolution,
                'format': format,
                'tbr': tbr,
                'height': height,
                'format_id': format,
            })
        self._sort_formats(formats)

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'uploader': video_uploader,
            'title': video_title,
            'thumbnail': thumbnail,
            'description': description,
            'formats': formats,
            'age_limit': age_limit,
        }

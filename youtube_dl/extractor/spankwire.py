from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    sanitized_Request,
    str_to_int,
    int_or_none,
    unified_strdate,
)
from ..aes import aes_decrypt_text


class SpankwireIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>spankwire\.com/[^/]*/video(?P<id>[0-9]+)/?)'
    _TESTS = [{
        # download URL pattern: */<height>P_<tbr>K_<video_id>.mp4
        'url': 'http://www.spankwire.com/Buckcherry-s-X-Rated-Music-Video-Crazy-Bitch/video103545/',
        'md5': '8bbfde12b101204b39e4b9fe7eb67095',
        'info_dict': {
            'id': '103545',
            'ext': 'mp4',
            'title': 'Buckcherry`s X Rated Music Video Crazy Bitch',
            'description': 'Crazy Bitch X rated music video.',
            'uploader': 'oreusz',
            'uploader_id': '124697',
            'upload_date': '20070507',
            'age_limit': 18,
        }
    }, {
        # download URL pattern: */mp4_<format_id>_<video_id>.mp4
        'url': 'http://www.spankwire.com/Titcums-Compiloation-I/video1921551/',
        'md5': '09b3c20833308b736ae8902db2f8d7e6',
        'info_dict': {
            'id': '1921551',
            'ext': 'mp4',
            'title': 'Titcums Compiloation I',
            'description': 'cum on tits',
            'uploader': 'dannyh78999',
            'uploader_id': '3056053',
            'upload_date': '20150822',
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        req = sanitized_Request('http://www.' + mobj.group('url'))
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)
        json_req = sanitized_Request('https://www.spankwire.com/api/video/' + video_id + '.json')
        video_data = self._download_json(json_req, video_id)

        title = video_data['title']
        description = video_data['description']
        thumbnail = video_data['poster']

        uploader = self._search_regex(
            r'<a[^>]+class="uploaded__by"[^>]*>(.+?)</a>',
            webpage, 'uploader', flags=re.DOTALL, fatal=False)
        uploader_id = self._html_search_regex(
            r'by\s*<a href="/(?:user/viewProfile|Profile\.aspx)\?.*?UserId=(\d+).*?"',
            webpage, 'uploader id', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            # r'</a> on (.+?) at \d+:\d+',
            r'</span>(.+?) at \d+:\d+ (AM|PM) by',
            webpage, 'upload date', fatal=False))

        view_count = int_or_none(video_data['viewed'])
        comment_count = int_or_none(video_data['comments'])

        formats = []
        videos = video_data['videos']
        for quality, video_url in videos.items():
            height = quality.split('_')[1].replace('p', '')
            self.to_screen(height)
            formats.append({
                'url': video_url,
                'format_id': quality,
                'height': int_or_none(height),
                'tbr': None
            })
        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'view_count': view_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': age_limit,
        }

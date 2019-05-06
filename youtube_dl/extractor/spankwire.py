from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
    unified_strdate,
)
from youtube_dl.aes import aes_decrypt_text
from youtube_dl.compat import (
    compat_urllib_parse_urlparse,
    compat_urllib_parse_unquote,
)


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
        webpage = self._download_webpage(req, video_id, fatal=False)
        video_data = self._download_json('https://www.spankwire.com/api/video/' +
                                         video_id + '.json', video_id)

        title = video_data.get('title') or self._html_search_regex(
            r'<h1>([^<]+)', webpage, 'title')
        thumbnail = video_data.get('poster')
        description = video_data.get('description')

        uploader = self._search_regex(
            re.compile(r'<a[^>]+class="uploaded__by"[^>]*>(.+?)</a>', re.DOTALL),
            webpage, 'uploader', fatal=False)

        uploader_id = self._html_search_regex(
            r'by\s*<a href="/(?:user/viewProfile|Profile\.aspx)\?.*?UserId=(\d+).*?"',
            webpage, 'uploader id', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            r'</span>(.+?) at \d+:\d+ (?:AM|PM) by',
            webpage, 'upload date', fatal=False))

        view_count = int_or_none(video_data.get('viewed'))
        comment_count = int_or_none(video_data.get('comments'))
        duration = int_or_none(video_data.get('duration'))

        def extract_list(arr):
            names = []
            if arr:
                for i in arr:
                    names.append(i.get('name'))
            return names

        categories = extract_list(video_data.get('categories'))
        tags = extract_list(video_data.get('tags'))

        formats = []
        videos = re.findall(
            r'playerData\.cdnPath([0-9]{3,})\s*=\s*(?:encodeURIComponent\()?["\']([^"\']+)["\']', webpage)
        if videos:
            heights = [int(video[0]) for video in videos]
            video_urls = list(map(compat_urllib_parse_unquote, [video[1] for video in videos]))
            if webpage.find(r'flashvars\.encrypted = "true"') != -1:
                password = self._search_regex(
                    r'flashvars\.video_title = "([^"]+)',
                    webpage, 'password').replace('+', ' ')
                video_urls = list(map(
                    lambda s: aes_decrypt_text(s, password, 32).decode('utf-8'),
                    video_urls))

            for height, video_url in zip(heights, video_urls):
                path = compat_urllib_parse_urlparse(video_url).path
                m = re.search(r'/(?P<height>\d+)[pP]_(?P<tbr>\d+)[kK]', path)
                if m:
                    tbr = int(m.group('tbr'))
                    height = int(m.group('height'))
                else:
                    tbr = None
                formats.append({
                    'url': video_url,
                    'format_id': '%dp' % height,
                    'height': height,
                    'tbr': tbr,
                })
        else:
            for quality, video_url in video_data.get('videos').items():
                height = quality.replace('quality_', '').replace('p', '')
                formats.append({
                    'url': video_url,
                    'format_id': quality,
                    'height': int_or_none(height),
                })
        self._sort_formats(formats)

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
            'duration': duration,
            'categories': categories,
            'tags': tags,
        }

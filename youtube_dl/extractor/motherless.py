from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from ..utils import (
    str_to_int,
    unified_strdate,
)


class MotherlessIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?motherless\.com/(?:g/[a-z0-9_]+/)?(?P<id>[A-Z0-9]+)'
    _TESTS = [
        {
            'url': 'http://motherless.com/AC3FFE1',
            'md5': '310f62e325a9fafe64f68c0bccb6e75f',
            'info_dict': {
                'id': 'AC3FFE1',
                'ext': 'mp4',
                'title': 'Fucked in the ass while playing PS3',
                'categories': ['Gaming', 'anal', 'reluctant', 'rough', 'Wife'],
                'upload_date': '20100913',
                'uploader_id': 'famouslyfuckedup',
                'thumbnail': 're:http://.*\.jpg',
                'age_limit': 18,
            }
        },
        {
            'url': 'http://motherless.com/532291B',
            'md5': 'bc59a6b47d1f958e61fbd38a4d31b131',
            'info_dict': {
                'id': '532291B',
                'ext': 'mp4',
                'title': 'Amazing girl playing the omegle game, PERFECT!',
                'categories': ['Amateur', 'webcam', 'omegle', 'pink', 'young', 'masturbate', 'teen', 'game', 'hairy'],
                'upload_date': '20140622',
                'uploader_id': 'Sulivana7x',
                'thumbnail': 're:http://.*\.jpg',
                'age_limit': 18,
            }
        },
        {
            'url': 'http://motherless.com/g/cosplay/633979F',
            'md5': '0b2a43f447a49c3e649c93ad1fafa4a0',
            'info_dict': {
                'id': '633979F',
                'ext': 'mp4',
                'title': 'Turtlette',
                'categories': ['superheroine heroine  superher'],
                'upload_date': '20140827',
                'uploader_id': 'shade0230',
                'thumbnail': 're:http://.*\.jpg',
                'age_limit': 18,
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'id="view-upload-title">\s+([^<]+)<', webpage, 'title')
        video_url = self._html_search_regex(
            r'setup\(\{\s+"file".+: "([^"]+)",', webpage, 'video URL')
        age_limit = self._rta_search(webpage)
        view_count = str_to_int(self._html_search_regex(
            r'<strong>Views</strong>\s+([^<]+)<',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._html_search_regex(
            r'<strong>Favorited</strong>\s+([^<]+)<',
            webpage, 'like count', fatal=False))

        upload_date = self._html_search_regex(
            r'<strong>Uploaded</strong>\s+([^<]+)<', webpage, 'upload date')
        if 'Ago' in upload_date:
            days = int(re.search(r'([0-9]+)', upload_date).group(1))
            upload_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
        else:
            upload_date = unified_strdate(upload_date)

        comment_count = webpage.count('class="media-comment-contents"')
        uploader_id = self._html_search_regex(
            r'"thumb-member-username">\s+<a href="/m/([^"]+)"',
            webpage, 'uploader_id')

        categories = self._html_search_meta('keywords', webpage)
        if categories:
            categories = [cat.strip() for cat in categories.split(',')]

        return {
            'id': video_id,
            'title': title,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'categories': categories,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'age_limit': age_limit,
            'url': video_url,
        }

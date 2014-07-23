from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class MotherlessIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?motherless\.com/(?P<id>[A-Z0-9]+)'
    _TESTS = [
        {
            'url': 'http://motherless.com/AC3FFE1',
            'md5': '5527fef81d2e529215dad3c2d744a7d9',
            'info_dict': {
                'id': 'AC3FFE1',
                'ext': 'flv',
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
        }
    ]

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'id="view-upload-title">\s+([^<]+)<', webpage, 'title')
        
        video_url = self._html_search_regex(r'setup\(\{\s+"file".+: "([^"]+)",', webpage, 'video_url')
        age_limit = self._rta_search(webpage)

        view_count = self._html_search_regex(r'<strong>Views</strong>\s+([^<]+)<', webpage, 'view_count')
 
        upload_date = self._html_search_regex(r'<strong>Uploaded</strong>\s+([^<]+)<', webpage, 'upload_date')
        if 'Ago' in upload_date:
            days = int(re.search(r'([0-9]+)', upload_date).group(1))
            upload_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
        else:
            upload_date = unified_strdate(upload_date)

        like_count = self._html_search_regex(r'<strong>Favorited</strong>\s+([^<]+)<', webpage, 'like_count')

        comment_count = webpage.count('class="media-comment-contents"')
        uploader_id = self._html_search_regex(r'"thumb-member-username">\s+<a href="/m/([^"]+)"', webpage, 'uploader_id')

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
            'view_count': int_or_none(view_count.replace(',', '')),
            'like_count': int_or_none(like_count.replace(',', '')),
            'comment_count': comment_count,
            'age_limit': age_limit,
            'url': video_url,
        }

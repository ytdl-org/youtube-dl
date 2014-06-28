from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from ..utils import str_to_int


class MotherlessIE(InfoExtractor):
    """Information Extractor for Motherless"""
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
                'thumbnail': 'http://thumbs.motherlessmedia.com/thumbs/AC3FFE1.jpg',
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
                'thumbnail': 'http://thumbs.motherlessmedia.com/thumbs/532291B.jpg',
                'age_limit': 18,
            }
        }
    ]

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(?P<title>.+?) - MOTHERLESS.COM</title>', webpage, 'title')
        video_url = self._search_regex(r"__fileurl = '(?P<video_url>[^']+)'", webpage, 'video_url')
        thumbnail = self._og_search_thumbnail(webpage)
        age_limit = self._rta_search(webpage)  # Hint: it's 18 ;)
        view_count = str_to_int(self._html_search_regex(r'<strong>Views</strong>(.+?)</h2>', webpage,
                                                        'view_count', flags=re.DOTALL))

        like_count = str_to_int(self._html_search_regex(r'<strong>Favorited</strong>(.+?)</h2>', webpage,
                                                        'like_count', flags=re.DOTALL))
        comment_count = webpage.count('class="media-comment-contents"')
        uploader_id = self._html_search_regex(r'<div class="thumb-member-username">.*?<a [^>]*>(.+?)</a>',
                                              webpage, 'uploader_id', flags=re.DOTALL)

        categories = self._html_search_meta('keywords', webpage)
        if categories is not None:
            categories = [cat.strip() for cat in categories.split(',')]

        upload_date = self._html_search_regex(r'<strong>Uploaded</strong>(.+?)</h2>', webpage,
                                              'upload_date', flags=re.DOTALL)
        mobj = re.search(r'(\d+) days? ago', upload_date, re.I)
        if mobj is not None:
            upload_date = datetime.datetime.now() - datetime.timedelta(days=int(mobj.group(1)))
        else:
            mobj = re.search(r'(\w+) (\d+)\w* (\d+)', upload_date, re.I)
            if mobj is not None:
                upload_date = datetime.datetime.strptime('%s %s %s' % mobj.groups(), '%b %d %Y').date()
            else:
                upload_date = None
        if upload_date is not None:
            upload_date = upload_date.strftime('%Y%m%d')

        return {
            'id': video_id,
            'title': title,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
            'categories': categories,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'age_limit': age_limit,
            'url': video_url,
        }

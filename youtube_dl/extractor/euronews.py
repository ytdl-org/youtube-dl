# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    remove_end,
    unified_strdate,
)


class EuronewsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:[a-z]+\.)?euronews\.com/(?P<id>\d+/\d+/\d+/[^/]+$)'
    _TESTS = [{
        'url': 'http://de.euronews.com/2017/01/24/the-brief-from-brussels-martin-schulz-tritt-gegen-angela-merkel-an',
        'md5': '32d56fdbe4778354ff4afcd0ef97c1c8',
        'info_dict': {
            'id': '2017/01/24/the-brief-from-brussels-martin-schulz-tritt-gegen-angela-merkel-an',
            'ext': 'mp4',
            'title': 'The Brief from Brussels: Martin Schulz tritt gegen Angela Merkel an',
            'description': 'md5:a49ceceb9f277cd93a4836bfc54498f1',
            'upload_date': '20170124',
            'thumbnail': 'http://static.euronews.com/articles/355867/1000x563_355867.jpg',
        },
    }, {
        'url': 'http://www.euronews.com/2017/01/25/team-usa-takes-gold-at-chef-olympics-in-france',
        'info_dict': {
            'id': '2017/01/25/team-usa-takes-gold-at-chef-olympics-in-france',
            'ext': 'mp4',
            'title': '''Team USA takes gold at 'Chef Olympics' in France''',
            'description': 'md5:a1d7f4dd524a46a66d201e0634dc5aee',
            'upload_date': '20170125',
            'thumbnail': 'http://static.euronews.com/articles/356014/1000x563_356014.jpg'
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        if title:
            title = remove_end(title, '| Euronews').strip()
        description = self._og_search_description(webpage)

        video_url = self._og_search_video_url(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        upload_date = self._html_search_meta('date.created', webpage)
        if upload_date:
            upload_date = unified_strdate(upload_date)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
        }

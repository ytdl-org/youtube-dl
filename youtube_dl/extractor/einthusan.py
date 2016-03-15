# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    remove_start,
    sanitized_Request,
)


class EinthusanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?einthusan\.com/movies/watch.php\?([^#]*?)id=(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.einthusan.com/movies/watch.php?id=2447',
            'md5': 'af244f4458cd667205e513d75da5b8b1',
            'info_dict': {
                'id': '2447',
                'ext': 'mp4',
                'title': 'Ek Villain',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'md5:9d29fc91a7abadd4591fb862fa560d93',
            }
        },
        {
            'url': 'http://www.einthusan.com/movies/watch.php?id=1671',
            'md5': 'ef63c7a803e22315880ed182c10d1c5c',
            'info_dict': {
                'id': '1671',
                'ext': 'mp4',
                'title': 'Soodhu Kavvuum',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'md5:05d8a0c0281a4240d86d76e14f2f4d51',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = sanitized_Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0')
        webpage = self._download_webpage(request, video_id)

        title = self._html_search_regex(
            r'<h1><a[^>]+class=["\']movie-title["\'][^>]*>(.+?)</a></h1>',
            webpage, 'title')

        video_id = self._search_regex(
            r'data-movieid=["\'](\d+)', webpage, 'video id', default=video_id)

        video_url = self._download_webpage(
            'http://cdn.einthusan.com/geturl/%s/hd/London,Washington,Toronto,Dallas,San,Sydney/'
            % video_id, video_id)

        description = self._html_search_meta('description', webpage)
        thumbnail = self._html_search_regex(
            r'''<a class="movie-cover-wrapper".*?><img src=["'](.*?)["'].*?/></a>''',
            webpage, "thumbnail url", fatal=False)
        if thumbnail is not None:
            thumbnail = compat_urlparse.urljoin(url, remove_start(thumbnail, '..'))

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
        }

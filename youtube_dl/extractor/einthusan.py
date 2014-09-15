# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


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
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(
            r'<h1><a class="movie-title".*?>(.*?)</a></h1>', webpage, 'title')

        video_url = self._html_search_regex(
            r'''(?s)jwplayer\("mediaplayer"\)\.setup\({.*?'file': '([^']+)'.*?}\);''',
            webpage, 'video url')

        description = self._html_search_meta('description', webpage)
        thumbnail = self._html_search_regex(
            r'''<a class="movie-cover-wrapper".*?><img src=["'](.*?)["'].*?/></a>''',
            webpage, "thumbnail url", fatal=False)
        if thumbnail is not None:
            thumbnail = thumbnail.replace('..', 'http://www.einthusan.com')

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
        }

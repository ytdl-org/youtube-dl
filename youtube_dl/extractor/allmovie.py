# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class AllmovieIE(InfoExtractor):
    """Information extractor for allmovie.tv

    Test with:
        python test/test_download.py TestDownload.test_Allmovie

    """
    _VALID_URL = r'http://allmovie\.tv/video/.+-(?P<id>\d+)\.html'

    _TEST = {
        'url': 'http://allmovie.tv/video/vesti-v-subbotu-28-10-2017-17255.html',
        'md5': '5e9a21314b8dfd472c1a9cd61c610dd6',
        'info_dict': {
            'id': '17255',
            'ext': 'mp4',
            'title': 'Вести в субботу 28.10.2017',
            'description': 'Вести в субботу 28.10.2017',
            'thumbnail': 'http://allmovie.tv/upload/video/images/small/1d/d7/1dd757d37eb1431f541839d30371d436.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page_info = self._download_webpage(url, video_id, note='Downloading info page ...')

        page_player = self._download_webpage(
            'http://allmovie.tv/video/show_player/%s' % video_id, video_id,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            note='Downloading player page ...')

        video_url = self._search_regex(r'source src="([^"]+)"', page_player, 'video URL')

        return {
            'id': video_id,
            'title': self._og_search_title(page_info),
            'description': self._og_search_description(page_info),
            'thumbnail': self._og_search_thumbnail(page_info),
            'url': video_url,
        }

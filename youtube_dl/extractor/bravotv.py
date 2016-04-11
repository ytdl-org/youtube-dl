# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class BravoTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bravotv\.com/(?:[^/]+/)+videos/(?P<id>[^/?]+)'
    _TEST = {
        'url': 'http://www.bravotv.com/last-chance-kitchen/season-5/videos/lck-ep-12-fishy-finale',
        'md5': 'd60cdf68904e854fac669bd26cccf801',
        'info_dict': {
            'id': 'LitrBdX64qLn',
            'ext': 'mp4',
            'title': 'Last Chance Kitchen Returns',
            'description': 'S13: Last Chance Kitchen Returns for Top Chef Season 13',
            'timestamp': 1448926740,
            'upload_date': '20151130',
            'uploader': 'NBCU-BRAV',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        account_pid = self._search_regex(r'"account_pid"\s*:\s*"([^"]+)"', webpage, 'account pid')
        release_pid = self._search_regex(r'"release_pid"\s*:\s*"([^"]+)"', webpage, 'release pid')
        return self.url_result(smuggle_url(
            'http://link.theplatform.com/s/%s/%s?mbr=true&switch=progressive' % (account_pid, release_pid),
            {'force_smil_url': True}), 'ThePlatform', release_pid)

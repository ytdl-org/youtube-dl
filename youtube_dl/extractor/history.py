from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class HistoryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?history\.com/(?:[^/]+/)+(?P<id>[^/]+?)(?:$|[?#])'

    _TESTS = [{
        'url': 'http://www.history.com/topics/valentines-day/history-of-valentines-day/videos/bet-you-didnt-know-valentines-day?m=528e394da93ae&s=undefined&f=1&free=false',
        'md5': '6fe632d033c92aa10b8d4a9be047a7c5',
        'info_dict': {
            'id': 'bLx5Dv5Aka1G',
            'ext': 'mp4',
            'title': "Bet You Didn't Know: Valentine's Day",
            'description': 'md5:7b57ea4829b391995b405fa60bd7b5f7',
        },
        'add_ie': ['ThePlatform'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'data-href="[^"]*/%s"[^>]+data-release-url="([^"]+)"' % video_id,
            webpage, 'video url')

        return self.url_result(smuggle_url(video_url, {'sig': {'key': 'crazyjava', 'secret': 's3cr3t'}}))

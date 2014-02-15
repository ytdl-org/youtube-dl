from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SyfyIE(InfoExtractor):
    _VALID_URL = r'https?://www\.syfy\.com/videos/.+?vid:(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.syfy.com/videos/Robot%20Combat%20League/Behind%20the%20Scenes/vid:2631458',
        'md5': 'e07de1d52c7278adbb9b9b1c93a66849',
        'info_dict': {
            'id': 'NmqMrGnXvmO1',
            'ext': 'flv',
            'title': 'George Lucas has Advice for his Daughter',
            'description': 'Listen to what insights George Lucas give his daughter Amanda.',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        return self.url_result(self._og_search_video_url(webpage))

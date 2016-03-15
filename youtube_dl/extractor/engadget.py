from __future__ import unicode_literals

from .common import InfoExtractor


class EngadgetIE(InfoExtractor):
    _VALID_URL = r'https?://www.engadget.com/video/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.engadget.com/video/518153925/',
        'md5': 'c6820d4828a5064447a4d9fc73f312c9',
        'info_dict': {
            'id': '518153925',
            'ext': 'mp4',
            'title': 'Samsung Galaxy Tab Pro 8.4 Review',
        },
        'add_ie': ['FiveMin'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result('5min:%s' % video_id)

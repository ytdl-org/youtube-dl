from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SyfyIE(InfoExtractor):
    _VALID_URL = r'https?://www\.syfy\.com/(?:videos/.+?vid:(?P<id>[0-9]+)|(?!videos)(?P<video_name>[^/]+)(?:$|[?#]))'

    _TESTS = [{
        'url': 'http://www.syfy.com/videos/Robot%20Combat%20League/Behind%20the%20Scenes/vid:2631458',
        'info_dict': {
            'id': 'NmqMrGnXvmO1',
            'ext': 'flv',
            'title': 'George Lucas has Advice for his Daughter',
            'description': 'Listen to what insights George Lucas give his daughter Amanda.',
        },
        'add_ie': ['ThePlatform'],
    }, {
        'url': 'http://www.syfy.com/wilwheaton',
        'md5': '94dfa54ee3ccb63295b276da08c415f6',
        'info_dict': {
            'id': '4yoffOOXC767',
            'ext': 'flv',
            'title': 'The Wil Wheaton Project - Premiering May 27th at 10/9c.',
            'description': 'The Wil Wheaton Project premieres May 27th at 10/9c. Don\'t miss it.',
        },
        'add_ie': ['ThePlatform'],
        'skip': 'Blocked outside the US',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_name = mobj.group('video_name')
        if video_name:
            generic_webpage = self._download_webpage(url, video_name)
            video_id = self._search_regex(
                r'<iframe.*?class="video_iframe_page"\s+src="/_utils/video/thP_video_controller.php.*?_vid([0-9]+)">',
                generic_webpage, 'video ID')
            url = 'http://www.syfy.com/videos/%s/%s/vid:%s' % (
                video_name, video_name, video_id)
        else:
            video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        return self.url_result(self._og_search_video_url(webpage))

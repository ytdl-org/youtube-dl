from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import find_xpath_attr, compat_str


class NBCIE(InfoExtractor):
    _VALID_URL = r'http://www\.nbc\.com/[^/]+/video/[^/]+/(?P<id>n?\d+)'

    _TEST = {
        'url': 'http://www.nbc.com/chicago-fire/video/i-am-a-firefighter/2734188',
        'md5': '54d0fbc33e0b853a65d7b4de5c06d64e',
        'info_dict': {
            'id': 'u1RInQZRN7QJ',
            'ext': 'flv',
            'title': 'I Am a Firefighter',
            'description': 'An emergency puts Dawson\'sf irefighter skills to the ultimate test in this four-part digital series.',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        theplatform_url = self._search_regex('class="video-player video-player-full" data-mpx-url="(.*?)"', webpage, 'theplatform url')
        if theplatform_url.startswith('//'):
            theplatform_url = 'http:' + theplatform_url
        return self.url_result(theplatform_url)


class NBCNewsIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nbcnews\.com/video/.+?/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.nbcnews.com/video/nbc-news/52753292',
        'md5': '47abaac93c6eaf9ad37ee6c4463a5179',
        'info_dict': {
            'id': '52753292',
            'ext': 'flv',
            'title': 'Crew emerges after four-month Mars food study',
            'description': 'md5:24e632ffac72b35f8b67a12d1b6ddfc1',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        all_info = self._download_xml('http://www.nbcnews.com/id/%s/displaymode/1219' % video_id, video_id)
        info = all_info.find('video')

        return {
            'id': video_id,
            'title': info.find('headline').text,
            'ext': 'flv',
            'url': find_xpath_attr(info, 'media', 'type', 'flashVideo').text,
            'description': compat_str(info.find('caption').text),
            'thumbnail': find_xpath_attr(info, 'media', 'type', 'thumbnail').text,
        }

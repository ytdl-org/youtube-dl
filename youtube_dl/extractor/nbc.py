from __future__ import unicode_literals

import re
import json

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
    _VALID_URL = r'''(?x)https?://www\.nbcnews\.com/
        ((video/.+?/(?P<id>\d+))|
        (feature/[^/]+/(?P<title>.+)))
        '''

    _TESTS = [
        {
            'url': 'http://www.nbcnews.com/video/nbc-news/52753292',
            'md5': '47abaac93c6eaf9ad37ee6c4463a5179',
            'info_dict': {
                'id': '52753292',
                'ext': 'flv',
                'title': 'Crew emerges after four-month Mars food study',
                'description': 'md5:24e632ffac72b35f8b67a12d1b6ddfc1',
            },
        },
        {
            'url': 'http://www.nbcnews.com/feature/edward-snowden-interview/how-twitter-reacted-snowden-interview-n117236',
            'md5': 'b2421750c9f260783721d898f4c42063',
            'info_dict': {
                'id': 'I1wpAI_zmhsQ',
                'ext': 'flv',
                'title': 'How Twitter Reacted To The Snowden Interview',
                'description': 'md5:65a0bd5d76fe114f3c2727aa3a81fe64',
            },
            'add_ie': ['ThePlatform'],
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        if video_id is not None:
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
        else:
            # "feature" pages use theplatform.com
            title = mobj.group('title')
            webpage = self._download_webpage(url, title)
            bootstrap_json = self._search_regex(
                r'var bootstrapJson = ({.+})\s*$', webpage, 'bootstrap json',
                flags=re.MULTILINE)
            bootstrap = json.loads(bootstrap_json)
            info = bootstrap['results'][0]['video']
            playlist_url = info['fallbackPlaylistUrl'] + '?form=MPXNBCNewsAPI'
            mpxid = info['mpxId']
            all_videos = self._download_json(playlist_url, title)['videos']
            # The response contains additional videos
            info = next(v for v in all_videos if v['mpxId'] == mpxid)

            return {
                '_type': 'url',
                # We get the best quality video
                'url': info['videoAssets'][-1]['publicUrl'],
                'ie_key': 'ThePlatform',
            }

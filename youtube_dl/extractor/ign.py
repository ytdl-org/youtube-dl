import re
import json

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)

class IGNIE(InfoExtractor):
    _VALID_URL = r'http://www.ign.com/videos/.+/(?P<name>.+)'
    IE_NAME = u'ign.com'

    _TEST = {
        u'url': u'http://www.ign.com/videos/2013/06/05/the-last-of-us-review',
        u'file': u'8f862beef863986b2785559b9e1aa599.mp4',
        u'md5': u'eac8bdc1890980122c3b66f14bdd02e9',
        u'info_dict': {
            u'title': u'The Last of Us Review',
            u'description': u'md5:c8946d4260a4d43a00d5ae8ed998870c',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        config_url = url + '.config'
        webpage = self._download_webpage(url, name)
        config = json.loads(self._download_webpage(config_url, name, u'Downloading video info'))

        self.report_extraction(name)
        description = self._html_search_regex(r'<span class="page-object-description">(.+?)</span>',
                                              webpage, 'video description', flags=re.DOTALL)
        media = config['playlist']['media']
        video_url = media['url']

        return {'id': media['metadata']['videoId'],
                'url': video_url,
                'ext': determine_ext(video_url),
                'title': media['metadata']['title'],
                'description': description,
                'thumbnail': media['poster'][0]['url'].replace('{size}', 'small'),
                }
        



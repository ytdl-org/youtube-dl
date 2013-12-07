import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    determine_ext,
)


class MuzuTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.muzu\.tv/(.+?)/(.+?)/(?P<id>\d+)'
    IE_NAME = u'muzu.tv'

    _TEST = {
        u'url': u'http://www.muzu.tv/defected/marcashken-featuring-sos-cat-walk-original-mix-music-video/1981454/',
        u'file': u'1981454.mp4',
        u'md5': u'98f8b2c7bc50578d6a0364fff2bfb000',
        u'info_dict': {
            u'title': u'Cat Walk (Original Mix)',
            u'description': u'md5:90e868994de201b2570e4e5854e19420',
            u'uploader': u'MarcAshken featuring SOS',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        info_data = compat_urllib_parse.urlencode({'format': 'json',
                                                   'url': url,
                                                   })
        video_info_page = self._download_webpage('http://www.muzu.tv/api/oembed/?%s' % info_data,
                                                 video_id, u'Downloading video info')
        info = json.loads(video_info_page)

        player_info_page = self._download_webpage('http://player.muzu.tv/player/playerInit?ai=%s' % video_id,
                                                  video_id, u'Downloading player info')
        video_info = json.loads(player_info_page)['videos'][0]
        for quality in ['1080' , '720', '480', '360']:
            if video_info.get('v%s' % quality):
                break

        data = compat_urllib_parse.urlencode({'ai': video_id,
                                              # Even if each time you watch a video the hash changes,
                                              # it seems to work for different videos, and it will work
                                              # even if you use any non empty string as a hash
                                              'viewhash': 'VBNff6djeV4HV5TRPW5kOHub2k',
                                              'device': 'web',
                                              'qv': quality,
                                              })
        video_url_page = self._download_webpage('http://player.muzu.tv/player/requestVideo?%s' % data,
                                                video_id, u'Downloading video url')
        video_url_info = json.loads(video_url_page)
        video_url = video_url_info['url']

        return {'id': video_id,
                'title': info['title'],
                'url': video_url,
                'ext': determine_ext(video_url),
                'thumbnail': info['thumbnail_url'],
                'description': info['description'],
                'uploader': info['author_name'],
                }

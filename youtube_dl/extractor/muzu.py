from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)


class MuzuTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.muzu\.tv/(.+?)/(.+?)/(?P<id>\d+)'
    IE_NAME = 'muzu.tv'

    _TEST = {
        'url': 'http://www.muzu.tv/defected/marcashken-featuring-sos-cat-walk-original-mix-music-video/1981454/',
        'md5': '98f8b2c7bc50578d6a0364fff2bfb000',
        'info_dict': {
            'id': '1981454',
            'ext': 'mp4',
            'title': 'Cat Walk (Original Mix)',
            'description': 'md5:90e868994de201b2570e4e5854e19420',
            'uploader': 'MarcAshken featuring SOS',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info_data = compat_urllib_parse.urlencode({
            'format': 'json',
            'url': url,
        })
        info = self._download_json(
            'http://www.muzu.tv/api/oembed/?%s' % info_data,
            video_id, 'Downloading video info')

        player_info = self._download_json(
            'http://player.muzu.tv/player/playerInit?ai=%s' % video_id,
            video_id, 'Downloading player info')
        video_info = player_info['videos'][0]
        for quality in ['1080', '720', '480', '360']:
            if video_info.get('v%s' % quality):
                break

        data = compat_urllib_parse.urlencode({
            'ai': video_id,
            # Even if each time you watch a video the hash changes,
            # it seems to work for different videos, and it will work
            # even if you use any non empty string as a hash
            'viewhash': 'VBNff6djeV4HV5TRPW5kOHub2k',
            'device': 'web',
            'qv': quality,
        })
        video_url_info = self._download_json(
            'http://player.muzu.tv/player/requestVideo?%s' % data,
            video_id, 'Downloading video url')
        video_url = video_url_info['url']

        return {
            'id': video_id,
            'title': info['title'],
            'url': video_url,
            'thumbnail': info['thumbnail_url'],
            'description': info['description'],
            'uploader': info['author_name'],
        }

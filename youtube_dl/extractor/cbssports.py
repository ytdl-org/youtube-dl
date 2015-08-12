from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CBSSportsIE(InfoExtractor):
    _VALID_URL = r'http://www\.cbssports\.com/video/player/(?P<section>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.cbssports.com/video/player/tennis/482755139719/0/serena-williams-wins-2015-wimbledon-championship',
        'info_dict': {
            'id': 'GQGZp_4tBqW6',
            'ext': 'flv',
            'title': 'Serena Williams wins 2015 Wimbledon Championship',
            'description': 'Serena Williams completed the Serena Slam on Saturday and now holds all four major titles. Jamie Erdahl has the latest on what the win means for Serena.',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        section = mobj.group('section')
        video_id = mobj.group('id')
        all_videos = self._download_json(
            'http://www.cbssports.com/data/video/player/getVideos/%s?as=json' % section,
            video_id)
        # The json file contains the info of all the videos in the section
        video_info = next(v for v in all_videos if v['pcid'] == video_id)
        return self.url_result('theplatform:%s' % video_info['pid'], 'ThePlatform')

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CBSSportsIE(InfoExtractor):
    _VALID_URL = r'http://www\.cbssports\.com/video/player/(?P<section>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.cbssports.com/video/player/tennis/318462531970/0/us-open-flashbacks-1990s',
        'info_dict': {
            'id': '_d5_GbO8p1sT',
            'ext': 'flv',
            'title': 'US Open flashbacks: 1990s',
            'description': 'Bill Macatee relives the best moments in US Open history from the 1990s.',
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

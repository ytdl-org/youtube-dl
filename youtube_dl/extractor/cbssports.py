from __future__ import unicode_literals

from .cbs import CBSBaseIE


class CBSSportsIE(CBSBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cbssports\.com/video/player/[^/]+/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.cbssports.com/video/player/videos/708337219968/0/ben-simmons-the-next-lebron?-not-so-fast',
        'info_dict': {
            'id': '708337219968',
            'ext': 'mp4',
            'title': 'Ben Simmons the next LeBron? Not so fast',
            'description': 'md5:854294f627921baba1f4b9a990d87197',
            'timestamp': 1466293740,
            'upload_date': '20160618',
            'uploader': 'CBSI-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]

    def _extract_video_info(self, filter_query, video_id):
        return self._extract_feed_info('dJ5BDC', 'VxxJg8Ymh8sE', filter_query, video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._extract_video_info('byId=%s' % video_id, video_id)

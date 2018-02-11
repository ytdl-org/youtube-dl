# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GameInformerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gameinformer\.com/(?:[^/]+/)*(?P<id>.+)\.aspx'
    _TEST = {
        'url': 'http://www.gameinformer.com/b/features/archive/2015/09/26/replay-animal-crossing.aspx',
        'md5': '292f26da1ab4beb4c9099f1304d2b071',
        'info_dict': {
            'id': '4515472681001',
            'ext': 'mp4',
            'title': 'Replay - Animal Crossing',
            'description': 'md5:2e211891b215c85d061adc7a4dd2d930',
            'timestamp': 1443457610,
            'upload_date': '20150928',
            'uploader_id': '694940074001',
        },
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/694940074001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        brightcove_id = self._search_regex(r"getVideo\('[^']+video_id=(\d+)", webpage, 'brightcove id')
        return self.url_result(self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id)

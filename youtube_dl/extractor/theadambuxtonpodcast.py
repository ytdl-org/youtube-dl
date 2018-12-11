from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import url_or_none


class TheAdamBuxtonPodcastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?adam-buxton.co.uk/podcasts/(?P<id>.+)'
    _TESTS = [{
        'url': 'http://adam-buxton.co.uk/podcasts/ep32-tash-demetriou',
        'md5': '917af1ea59de06a4b4b138036303f57d',
        'info_dict': {
            'id': '289871919',
            'ext': 'mp3',
            'title': 'EP.32 - TASH DEMETRIOU',
            'upload_date': '20161025',
            'description': 'md5:7b752d1651e7ec5974dbefb9b6c9e018',
            'uploader': 'Adam Buxton'
        }
    }, {
        'url': 'http://adam-buxton.co.uk/podcasts/ep77-tim-key',
        'md5': '5e825b21eebf3b10beebf851ce429cdb',
        'info_dict': {
            'id': '45398950-21a3-4cff-8b77-833741e58686',
            'ext': 'mp3',
            'title': 'EP.77 - TIM KEY',
            'timestamp': 1528367852,
            'description': 'md5:b6b062c595de3149324bb0845783b864',
            'upload_date': '20180607'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        embedded_url = url_or_none(self._search_regex(r'(?s)<div[^>]+class="view-content".*?<iframe[^>]+src="([^"]+)"', webpage, 'iframe url', fatal=False))

        return {
            '_type': 'url',
            'url': embedded_url
        }

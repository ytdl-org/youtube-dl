from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse


class OReillyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?player\.oreilly\.com/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://player.oreilly.com/videos/9781491944639',
        'md5': '6382439f4bc1195bf395c91bd62b5671',
        'info_dict': {
            'id': '0_tz5u5q67',
            'title': '01_modern_data_strategy_mike_olson_cloudera_manuel_martin_marquez_cern',
            'ext': 'mp4',
            'upload_date': '20160602',
            'timestamp': 1464888738,
        }
    }, {
        'url': 'https://player.oreilly.com/embed/9781491944639',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://player.oreilly.com/embed/%s' % video_id

        webpage = self._download_webpage(url, video_id)

        partner_id = self._search_regex(r'var partnerId = \'([^\']+)\';',
            webpage, 'partner ID')
        kaltura_id = self._search_regex(r'var externalId = \'([^\']+)\';',
            webpage, 'Kaltura ID')
        title = self._search_regex(r'var title = \'([^\']+)\';',
            webpage, 'title')

        return self.url_result('kaltura:%s:%s' % (partner_id, kaltura_id),
            'Kaltura', video_title=title)

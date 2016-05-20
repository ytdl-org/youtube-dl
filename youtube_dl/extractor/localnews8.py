# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LocalNews8IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?localnews8\.com/.+?/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.localnews8.com/news/rexburg-business-turns-carbon-fiber-scraps-into-wedding-rings/35183304',
        'md5': '477bdb188f177788c65db27ecb56649b',
        'info_dict': {
            'id': '35183304',
            'ext': 'mp4',
            'title': 'Rexburg business turns carbon fiber scraps into wedding ring',
            'description': 'The process was first invented by Lamborghini and less than a dozen companies around the world use it.',
            'duration': '153',
            'timestamp': '1441844822',
            'uploader_id': 'api',
        }}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        partner_id = self._search_regex(r'partnerId\s*:\s*"(\d+)"', webpage, video_id)
        kaltura_id = self._search_regex(r'var\s+videoIdString\s*=\s*"kaltura:(.+)";', webpage, video_id)

        return self.url_result('kaltura:%s:%s' % (partner_id, kaltura_id), 'Kaltura')

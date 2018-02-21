# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BFMBusinessIE(InfoExtractor):
    _VALID_URL = r'https?://bfmbusiness\.bfmtv\.com/mediaplayer/video/.*?-(?P<id>[\d-]+).html'

    _TEST = {
        'url': 'http://bfmbusiness.bfmtv.com/mediaplayer/video/focus-sur-les-mathematiques-1902-1038229.html',
        'info_dict': {
            'id': '5737041255001',
            'ext': 'mp4',
            'title': 'Focus sur les mathématiques - 19/02',
            'uploader_id': '876450612001',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'only available for a week',
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/876450612001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        brightcove_id = self._search_regex(
            r'data-video-id=["\'](\d+)', webpage, 'brightcove id')
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew',
            brightcove_id)

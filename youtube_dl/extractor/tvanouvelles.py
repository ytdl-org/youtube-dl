# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
class TVANouvellesVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tvanouvelles\.ca/videos/(?P<id>[0-9]+)'
    _BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1741764581/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result(
            self._BRIGHTCOVE_URL_TEMPLATE % video_id,
            'BrightcoveNew', video_id)
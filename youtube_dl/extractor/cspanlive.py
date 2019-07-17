# coding: utf-8
from __future__ import unicode_literals

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import smuggle_url


class CSpanLiveIE(InfoExtractor):
    IE_NAME = 'cspanlive'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/3162030207001/2B2qWQJYYM_default/index.html?videoId=%s'

    _VALID_URL = r'^https?://(?:www\.)?c-span\.org/networks'

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'stream')

        akamai_token = self._html_search_regex(r'data-akamaitoken="([^"]+)"', webpage, 'akamai_token')
        video_id = self._html_search_regex(r'data-bcid="([^"]+)"', webpage, 'video_id')

        brightcove_url = smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % video_id, {
            'akamai_token': akamai_token,
            'source_url': url
        })

        return self.url_result(brightcove_url, ie=BrightcoveNewIE.ie_key(), video_id=video_id)

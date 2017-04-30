# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .brightcove import BrightcoveLegacyIE
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)


class RMCDecouverteIE(InfoExtractor):
    _VALID_URL = r'https?://rmcdecouverte\.bfmtv\.com/mediaplayer-replay.*?\bid=(?P<id>\d+)'

    _TEST = {
        'url': 'http://rmcdecouverte.bfmtv.com/mediaplayer-replay/?id=16548',
        'info_dict': {
            'id': '5411254766001',
            'ext': 'mp4',
            'title': '39/45:LE RESEAU DES FAUX BILLETS',
            'description': 'ic Brunet propose un nouvel \u00e9pisode des Grains de sable de l\'Histoire sur la plus grosse affaire de contrefa\u00e7on de la Seconde Guerre mondiale.',
            'uploader_id': '1969646226001',
            'upload_date': '20170426',
            'timestamp': 1493166610,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        'skip': 'Only works from France',
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1969646226001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        brightcove_legacy_url = BrightcoveLegacyIE._extract_brightcove_url(webpage)
        if brightcove_legacy_url:
            brightcove_id = compat_parse_qs(compat_urlparse.urlparse(brightcove_legacy_url).query)['@videoPlayer'][0]
        else:
            brightcove_id = self._search_regex(r'data-video-id="(.*?)"', webpage, 'brightcove_id')
        return self.url_result(self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id)

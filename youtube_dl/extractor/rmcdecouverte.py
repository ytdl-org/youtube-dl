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
        'url': 'http://rmcdecouverte.bfmtv.com/mediaplayer-replay/?id=1430&title=LES%20HEROS%20DU%2088e%20ETAGE',
        'info_dict': {
            'id': '5111223049001',
            'ext': 'mp4',
            'title': ': LES HEROS DU 88e ETAGE',
            'description': 'Découvrez comment la bravoure de deux hommes dans la Tour Nord du World Trade Center a sauvé  la vie d\'innombrables personnes le 11 septembre 2001.',
            'uploader_id': '1969646226001',
            'upload_date': '20160904',
            'timestamp': 1472951103,
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
        brightcove_id = compat_parse_qs(compat_urlparse.urlparse(brightcove_legacy_url).query)['@videoPlayer'][0]
        return self.url_result(self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id)

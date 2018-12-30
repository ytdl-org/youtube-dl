# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .brightcove import BrightcoveLegacyIE
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)


class RMCDecouverteIE(InfoExtractor):
    _VALID_URL = r'https?://rmcdecouverte\.bfmtv\.com/.+/program_(?P<id>\d+)'

    _TEST = {
        'url': 'https://rmcdecouverte.bfmtv.com/wheeler-dealers-occasions-a-saisir/program_2566/',
        'info_dict': {
            'id': '5983675500001',
            'ext': 'mp4',
            'title': 'CORVETTE',
            'description': 'md5:c1e8295521e45ffebf635d6a7658f506',
            'uploader_id': '1969646226001',
            'upload_date': '20181226',
            'timestamp': 1545861635,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'only available for a week',
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1969646226001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        brightcove_legacy_url = BrightcoveLegacyIE._extract_brightcove_url(webpage)
        if brightcove_legacy_url:
            brightcove_id = compat_parse_qs(compat_urlparse.urlparse(
                brightcove_legacy_url).query)['@videoPlayer'][0]
        else:
            brightcove_id = self._search_regex(
                r'data-video-id=["\'](\d+)', webpage, 'brightcove id')
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew',
            brightcove_id)

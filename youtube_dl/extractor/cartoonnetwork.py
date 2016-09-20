# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE


class CartoonNetworkIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cartoonnetwork\.com/video/(?:[^/]+/)+(?P<id>[^/?#]+)-(?:clip|episode)\.html'
    _TEST = {
        'url': 'http://www.cartoonnetwork.com/video/teen-titans-go/starfire-the-cat-lady-clip.html',
        'info_dict': {
            'id': '8a250ab04ed07e6c014ef3f1e2f9016c',
            'ext': 'mp4',
            'title': 'Starfire the Cat Lady',
            'description': 'Robin decides to become a cat so that Starfire will finally love him.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        id_type, video_id = re.search(r"_cnglobal\.cvp(Video|Title)Id\s*=\s*'([^']+)';", webpage).groups()
        query = ('id' if id_type == 'Video' else 'titleId') + '=' + video_id
        return self._extract_cvp_info(
            'http://www.cartoonnetwork.com/video-seo-svc/episodeservices/getCvpPlaylist?networkName=CN2&' + query, video_id, {
                'secure': {
                    'media_src': 'http://androidhls-secure.cdn.turner.com/toon/big',
                    'tokenizer_src': 'http://www.cartoonnetwork.com/cntv/mvpd/processors/services/token_ipadAdobe.do',
                },
            }, {
                'url': url,
                'site_name': 'CartoonNetwork',
                'auth_required': self._search_regex(
                    r'_cnglobal\.cvpFullOrPreviewAuth\s*=\s*(true|false);',
                    webpage, 'auth required', default='false') == 'true',
            })

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
        for line in webpage.splitlines():
            if "_cnglobal.currentVideo.mediaId" in line:
                simpleid = line.split('mediaId = "',1)[1]
                video_id = simpleid.replace('";', '')
            if "_cnglobal.currentVideo.episodeTitle" in line:
                simpletitle = line.split('episodeTitle = "',1)[1]
                title = simpletitle.replace('";', '')
            if "_cnglobal.currentVideo.authType" in line:
                simpleauth = line.split('authType = "',1)[1]
                auth = simpleauth.replace('";', '')
        if "auth" in auth:
                auth_required = 'true'
        if "unauth" in auth:
                auth_required = ''
        description = ''
        info = self._extract_ngtv_info(
            video_id,
            {'networkId': 'cartoonnetwork'},
            {
                'url': url,
                'site_name': 'CartoonNetwork',
                'auth_required': auth_required,
            },
        )
        info.update({
            'id': video_id,
            'title': title,
            'description': description,
        })
        return info

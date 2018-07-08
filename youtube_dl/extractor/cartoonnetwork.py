# coding: utf-8
from __future__ import unicode_literals

from .turner import TurnerBaseIE


class CartoonNetworkIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cartoonnetwork\.com/video/(?:[^/]+/)+(?P<id>[^/?#]+)-(?:clip|episode)\.html'
    _TEST = {
        'url': 'https://www.cartoonnetwork.com/video/steven-universe/we-are-the-crystal-gems-full-theme-song-music-video-episode.html',
        'info_dict': {
            'id': '7b1db96d17822fba0a3d1ba4b3c4071852a5078e',
            'ext': 'mp4',
            'title': 'We Are the Crystal Gems (Full Theme Song) Music Video',
            'description': 'Music and lyrics by Rebecca Sugar. Additional music by Jeff Liu, Steven Velema and Aivi Tran. Performed by Zach Callison, Estelle, Deedee Magno Hall, Michaela Dietz and Tom Scharpling.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(r"_cnglobal\.(cvpVideo|cvpTitle|videoMedia)Id\s*=\s*'([^']+)';", webpage, 'video_id', group=2)
        title = self._html_search_regex(r'og:title.*\scontent="([^"]+)"', webpage, 'title', group=1)
        description = self._html_search_regex(r'og:description.*\scontent="([^"]+)"', webpage, 'description', default=None, group=1)

        info = self._extract_ngtv_info(
            video_id,
            {'networkId': 'cartoonnetwork'},
            {
                'url': url,
                'site_name': 'CartoonNetwork',
                'auth_required': self._search_regex(
                    r'_cnglobal\.cvpFullOrPreviewAuth\s*=\s*(true|false);',
                    webpage, 'auth required', default='false') == 'true',
            },
        )
        info.update({
            'id': video_id,
            'title': title,
            'description': description,
        })
        return info

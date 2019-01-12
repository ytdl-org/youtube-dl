# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE

from ..utils import (
    int_or_none,
)

class CartoonNetworkIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cartoonnetwork\.com/video/(?:[^/]+/)+(?P<id>[^/?#]+)-(?:clip|episode)\.html'
    _TEST = {
        'url': 'https://www.cartoonnetwork.com/video/steven-universe/garnet-gets-a-job-clip.html',
        'info_dict': {
            'id': '96bc363957a17bc03d16feb86b8391a321f7e670',
            'ext': 'mp4',
            'title': 'Garnet Gets a Job',
            'description': 'Garnet and Steven explore the most unlikely timelines in Beach City.',
		},
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._html_search_regex(r'[^>]+.mediaId = "(.+?)"', webpage, 'video_id')	
        title = self._html_search_regex(r'[^>]+.episodeTitle = "(.+?)"', webpage, 'title')
        description = self._html_search_regex(r'[^>]+description[^>]*>(.+?)<', webpage, 'description', default=None)
        propertyName = self._html_search_regex(r'[^>]+.propertyName = "(.+?)"', webpage, 'propertyName', default=None)
        seriesId = self._html_search_regex(r'[^>]+.seriesId = "(.+?)"', webpage, 'seriesId', default=None)
        seasonNumber = self._html_search_regex(r'[^>]+.seasonNumber = "(.+?)"', webpage, 'seasonNumber', default=None)
        episodeNumber = self._html_search_regex(r'[^>]+.episodeNumber = "(.+?)"', webpage, 'episodeNumber', default=None)
        info = self._extract_ngtv_info(
            video_id,
            {'networkId': 'cartoonnetwork'},
            {
                'url': url,
                'site_name': 'CartoonNetwork',
                'auth_required': self._search_regex(
                    r'[^>]+currentVideo.authType = "(auth|unauth)"',
                    webpage, 'auth required', default='false') == 'auth',
            },
        )
        info.update({
            'id': video_id,
            'title': title,
            'description': description,
            'series': propertyName,
            'season_number': int_or_none(seasonNumber),
            'season_id': int_or_none(seriesId),
            'episode_number': int_or_none(episodeNumber),
        })
        return info

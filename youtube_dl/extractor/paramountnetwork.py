from __future__ import unicode_literals

import re

from .mtv import MTVServicesInfoExtractor


class ParamountNetworkIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?paramountnetwork\.com/[^/]+/[\da-z]{6}(?:[/?#&]|$)'
    _TESTS = [{
        'url': 'http://www.paramountnetwork.com/video-clips/e1ktem/nobodies-gangbanged',
        'md5': 'f53ab001b5c1c6fee01bc9f00e2859d1',
        'info_dict': {
            'id': 'e1ktem',
            'ext': 'mp4',
            'title': 'Gangbanged - NOBODIES | Paramount Network',
            'description': 'TODO: Add description checksum',
            'upload_date': 'TODO: Add upload date',
        },
    }, {
        'url': 'http://www.paramountnetwork.com/episodes/j830qm/lip-sync-battle-joel-mchale-vs-jim-rash-season-2-ep-13',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'j830qm',
            'ext': 'mp4',
            'title': 'Lip Sync Battle - Season 2, Ep. 13 - Joel McHale Vs. Jim Rash - Full Episode | Paramount Network',
            'description': 'TODO: Add description checksum',
        },
    }]

    _FEED_URL = 'http://www.spike.com/feeds/mrss/'
    _MOBILE_TEMPLATE = 'http://m.spike.com/videos/video.rbml?id=%s'
    _CUSTOM_URL_REGEX = re.compile(r'spikenetworkapp://([^/]+/[-a-fA-F0-9]+)')
    _GEO_COUNTRIES = ['US']

    def _extract_mgid(self, webpage):
        mgid = super(ParamountNetworkIE, self)._extract_mgid(webpage)
        if mgid is None:
            url_parts = self._search_regex(self._CUSTOM_URL_REGEX, webpage, 'episode_id')
            video_type, episode_id = url_parts.split('/', 1)
            mgid = 'mgid:arc:{0}:spike.com:{1}'.format(video_type, episode_id)
        return mgid

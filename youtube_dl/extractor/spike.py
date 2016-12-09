from __future__ import unicode_literals

import re

from .mtv import MTVServicesInfoExtractor


class SpikeIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?spike\.com/[^/]+/[\da-z]{6}(?:[/?#&]|$)'
    _TESTS = [{
        'url': 'http://www.spike.com/video-clips/lhtu8m/auction-hunters-can-allen-ride-a-hundred-year-old-motorcycle',
        'md5': '1a9265f32b0c375793d6c4ce45255256',
        'info_dict': {
            'id': 'b9c8221a-4e50-479a-b86d-3333323e38ba',
            'ext': 'mp4',
            'title': 'Auction Hunters|December 27, 2013|4|414|Can Allen Ride A Hundred Year-Old Motorcycle?',
            'description': 'md5:fbed7e82ed5fad493615b3094a9499cb',
            'timestamp': 1388120400,
            'upload_date': '20131227',
        },
    }, {
        'url': 'http://www.spike.com/full-episodes/j830qm/lip-sync-battle-joel-mchale-vs-jim-rash-season-2-ep-209',
        'md5': 'b25c6f16418aefb9ad5a6cae2559321f',
        'info_dict': {
            'id': '37ace3a8-1df6-48be-85b8-38df8229e241',
            'ext': 'mp4',
            'title': 'Lip Sync Battle|April 28, 2016|2|209|Joel McHale Vs. Jim Rash|Act 1',
            'description': 'md5:a739ca8f978a7802f67f8016d27ce114',
        },
    }, {
        'url': 'http://www.spike.com/video-clips/lhtu8m/',
        'only_matching': True,
    }, {
        'url': 'http://www.spike.com/video-clips/lhtu8m',
        'only_matching': True,
    }, {
        'url': 'http://bellator.spike.com/fight/atwr7k/bellator-158-michael-page-vs-evangelista-cyborg',
        'only_matching': True,
    }, {
        'url': 'http://bellator.spike.com/video-clips/bw6k7n/bellator-158-foundations-michael-venom-page',
        'only_matching': True,
    }]

    _FEED_URL = 'http://www.spike.com/feeds/mrss/'
    _MOBILE_TEMPLATE = 'http://m.spike.com/videos/video.rbml?id=%s'
    _CUSTOM_URL_REGEX = re.compile(r'spikenetworkapp://([^/]+/[-a-fA-F0-9]+)')

    def _extract_mgid(self, webpage):
        mgid = super(SpikeIE, self)._extract_mgid(webpage, default=None)
        if mgid is None:
            url_parts = self._search_regex(self._CUSTOM_URL_REGEX, webpage, 'episode_id')
            video_type, episode_id = url_parts.split('/', 1)
            mgid = 'mgid:arc:{0}:spike.com:{1}'.format(video_type, episode_id)
        return mgid

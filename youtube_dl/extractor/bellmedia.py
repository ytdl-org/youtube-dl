# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BellMediaIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?
        (?P<domain>
            (?:
                ctv|
                tsn|
                bnn|
                thecomedynetwork|
                discovery|
                discoveryvelocity|
                sciencechannel|
                investigationdiscovery|
                animalplanet|
                bravo|
                mtv|
                space|
                etalk
            )\.ca|
            much\.com
        )/.*?(?:\bvid(?:eoid)?=|-vid|~|%7E|/(?:episode)?)(?P<id>[0-9]{6,})'''
    _TESTS = [{
        'url': 'http://www.ctv.ca/video/player?vid=706966',
        'md5': 'ff2ebbeae0aa2dcc32a830c3fd69b7b0',
        'info_dict': {
            'id': '706966',
            'ext': 'mp4',
            'title': 'Larry Day and Richard Jutras on the TIFF red carpet of \'Stonewall\'',
            'description': 'etalk catches up with Larry Day and Richard Jutras on the TIFF red carpet of "Stonewall”.',
            'upload_date': '20150919',
            'timestamp': 1442624700,
        },
        'expected_warnings': ['HTTP Error 404'],
    }, {
        'url': 'http://www.thecomedynetwork.ca/video/player?vid=923582',
        'only_matching': True,
    }, {
        'url': 'http://www.tsn.ca/video/expectations-high-for-milos-raonic-at-us-open~939549',
        'only_matching': True,
    }, {
        'url': 'http://www.bnn.ca/video/berman-s-call-part-two-viewer-questions~939654',
        'only_matching': True,
    }, {
        'url': 'http://www.ctv.ca/YourMorning/Video/S1E6-Monday-August-29-2016-vid938009',
        'only_matching': True,
    }, {
        'url': 'http://www.much.com/shows/atmidnight/episode948007/tuesday-september-13-2016',
        'only_matching': True,
    }, {
        'url': 'http://www.much.com/shows/the-almost-impossible-gameshow/928979/episode-6',
        'only_matching': True,
    }, {
        'url': 'http://www.ctv.ca/DCs-Legends-of-Tomorrow/Video/S2E11-Turncoat-vid1051430',
        'only_matching': True,
    }, {
        'url': 'http://www.etalk.ca/video?videoid=663455',
        'only_matching': True,
    }]
    _DOMAINS = {
        'thecomedynetwork': 'comedy',
        'discoveryvelocity': 'discvel',
        'sciencechannel': 'discsci',
        'investigationdiscovery': 'invdisc',
        'animalplanet': 'aniplan',
        'etalk': 'ctv',
    }

    def _real_extract(self, url):
        domain, video_id = re.match(self._VALID_URL, url).groups()
        domain = domain.split('.')[0]
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': '9c9media:%s_web:%s' % (self._DOMAINS.get(domain, domain), video_id),
            'ie_key': 'NineCNineMedia',
        }

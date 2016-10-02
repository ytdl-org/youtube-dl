from __future__ import unicode_literals

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

from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor


class SpikeIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://www\.spike\.com/(video-clips|episodes)/.+'
    _TEST = {
        'url': 'http://www.spike.com/video-clips/lhtu8m/auction-hunters-can-allen-ride-a-hundred-year-old-motorcycle',
        'md5': '1a9265f32b0c375793d6c4ce45255256',
        'info_dict': {
            'id': 'b9c8221a-4e50-479a-b86d-3333323e38ba',
            'ext': 'mp4',
            'title': 'Auction Hunters|Can Allen Ride A Hundred Year-Old Motorcycle?',
            'description': 'md5:fbed7e82ed5fad493615b3094a9499cb',
        },
    }

    _FEED_URL = 'http://www.spike.com/feeds/mrss/'

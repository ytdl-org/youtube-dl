from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor


class SouthParkIE(MTVServicesInfoExtractor):
    IE_NAME = 'southpark.cc.com'
    _VALID_URL = r'https?://(www\.)?(?P<url>southpark\.cc\.com/(clips|full-episodes)/(?P<id>.+?)(\?|#|$))'

    _FEED_URL = 'http://www.southparkstudios.com/feeds/video-player/mrss'

    _TESTS = [{
        'url': 'http://southpark.cc.com/clips/104437/bat-daded#tab=featured',
        'info_dict': {
            'id': 'a7bff6c2-ed00-11e0-aca6-0026b9414f30',
            'ext': 'mp4',
            'title': 'South Park|Bat Daded',
            'description': 'Randy disqualifies South Park by getting into a fight with Bat Dad.',
        },
    }]


class SouthparkDeIE(SouthParkIE):
    IE_NAME = 'southpark.de'
    _VALID_URL = r'https?://(www\.)?(?P<url>southpark\.de/(clips|alle-episoden)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://www.southpark.de/feeds/video-player/mrss/'

    _TESTS = [{
        'url': 'http://www.southpark.de/clips/uygssh/the-government-wont-respect-my-privacy#tab=featured',
        'info_dict': {
            'id': '85487c96-b3b9-4e39-9127-ad88583d9bf2',
            'ext': 'mp4',
            'title': 'The Government Won\'t Respect My Privacy',
            'description': 'Cartman explains the benefits of "Shitter" to Stan, Kyle and Craig.',
        },
    }]

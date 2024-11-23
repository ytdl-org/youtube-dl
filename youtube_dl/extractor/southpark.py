# coding: utf-8
from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor


class SouthParkIE(MTVServicesInfoExtractor):
    IE_NAME = 'southpark.cc.com'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark(?:\.cc|studios)\.com/(?:clips|(?:full-)?episodes|collections)/(?P<id>.+?)(\?|#|$))'

    _FEED_URL = 'http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed'

    _TESTS = [{
        'url': 'http://southpark.cc.com/clips/104437/bat-daded#tab=featured',
        'info_dict': {
            'id': 'a7bff6c2-ed00-11e0-aca6-0026b9414f30',
            'ext': 'mp4',
            'title': 'South Park|Bat Daded',
            'description': 'Randy disqualifies South Park by getting into a fight with Bat Dad.',
            'timestamp': 1112760000,
            'upload_date': '20050406',
        },
    }, {
        'url': 'http://southpark.cc.com/collections/7758/fan-favorites/1',
        'only_matching': True,
    }, {
        'url': 'https://www.southparkstudios.com/episodes/h4o269/south-park-stunning-and-brave-season-19-ep-1',
        'only_matching': True,
    }]

    def _get_feed_query(self, uri):
        return {
            'accountOverride': 'intl.mtvi.com',
            'arcEp': 'shared.southpark.global',
            'ep': '90877963',
            'imageEp': 'shared.southpark.global',
            'mgid': uri,
        }


class SouthParkEsIE(SouthParkIE):
    IE_NAME = 'southpark.cc.com:español'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark\.cc\.com/episodios-en-espanol/(?P<id>.+?)(\?|#|$))'
    _LANG = 'es'

    _TESTS = [{
        'url': 'http://southpark.cc.com/episodios-en-espanol/s01e01-cartman-consigue-una-sonda-anal#source=351c1323-0b96-402d-a8b9-40d01b2e9bde&position=1&sort=!airdate',
        'info_dict': {
            'title': 'Cartman Consigue Una Sonda Anal',
            'description': 'Cartman Consigue Una Sonda Anal',
        },
        'playlist_count': 4,
        'skip': 'Geo-restricted',
    }]


class SouthParkDeIE(SouthParkIE):
    IE_NAME = 'southpark.de'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark\.de/(?:clips|alle-episoden|collections)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://www.southpark.de/feeds/video-player/mrss/'

    _TESTS = [{
        'url': 'http://www.southpark.de/clips/uygssh/the-government-wont-respect-my-privacy#tab=featured',
        'info_dict': {
            'id': '85487c96-b3b9-4e39-9127-ad88583d9bf2',
            'ext': 'mp4',
            'title': 'South Park|The Government Won\'t Respect My Privacy',
            'description': 'Cartman explains the benefits of "Shitter" to Stan, Kyle and Craig.',
            'timestamp': 1380160800,
            'upload_date': '20130926',
        },
    }, {
        # non-ASCII characters in initial URL
        'url': 'http://www.southpark.de/alle-episoden/s18e09-hashtag-aufwärmen',
        'info_dict': {
            'title': 'Hashtag „Aufwärmen“',
            'description': 'Kyle will mit seinem kleinen Bruder Ike Videospiele spielen. Als der nicht mehr mit ihm spielen will, hat Kyle Angst, dass er die Kids von heute nicht mehr versteht.',
        },
        'playlist_count': 3,
    }, {
        # non-ASCII characters in redirect URL
        'url': 'http://www.southpark.de/alle-episoden/s18e09',
        'info_dict': {
            'title': 'Hashtag „Aufwärmen“',
            'description': 'Kyle will mit seinem kleinen Bruder Ike Videospiele spielen. Als der nicht mehr mit ihm spielen will, hat Kyle Angst, dass er die Kids von heute nicht mehr versteht.',
        },
        'playlist_count': 3,
    }, {
        'url': 'http://www.southpark.de/collections/2476/superhero-showdown/1',
        'only_matching': True,
    }]


class SouthParkNlIE(SouthParkIE):
    IE_NAME = 'southpark.nl'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark\.nl/(?:clips|(?:full-)?episodes|collections)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://www.southpark.nl/feeds/video-player/mrss/'

    _TESTS = [{
        'url': 'http://www.southpark.nl/full-episodes/s18e06-freemium-isnt-free',
        'info_dict': {
            'title': 'Freemium Isn\'t Free',
            'description': 'Stan is addicted to the new Terrance and Phillip mobile game.',
        },
        'playlist_mincount': 3,
    }]


class SouthParkDkIE(SouthParkIE):
    IE_NAME = 'southparkstudios.dk'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southparkstudios\.(?:dk|nu)/(?:clips|full-episodes|collections)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://www.southparkstudios.dk/feeds/video-player/mrss/'

    _TESTS = [{
        'url': 'http://www.southparkstudios.dk/full-episodes/s18e07-grounded-vindaloop',
        'info_dict': {
            'title': 'Grounded Vindaloop',
            'description': 'Butters is convinced he\'s living in a virtual reality.',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'http://www.southparkstudios.dk/collections/2476/superhero-showdown/1',
        'only_matching': True,
    }, {
        'url': 'http://www.southparkstudios.nu/collections/2476/superhero-showdown/1',
        'only_matching': True,
    }]

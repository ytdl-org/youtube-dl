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


class SouthParkDeIE(MTVServicesInfoExtractor):
    IE_NAME = 'southpark.de'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark\.de/(?:videoclip|folgen|collections)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed'
    _LANG = 'de'

    _TESTS = [{
        # clip
        'url': 'https://www.southpark.de/videoclip/ct46op/south-park-zahnfee-cartman',
        'info_dict': {
            'id': 'e99d45ea-ed00-11e0-aca6-0026b9414f30',
            'ext': 'mp4',
            'title': 'Zahnfee Cartman',
            'description': 'Cartman verkleidet sich als Zahnfee, um Butters unter dem Kissen liegenden Zahn zu stehlen. Cartman bekommt 4$ für diesen Zahn, was das Streben nach mehr Zähnen nährt'
        },
    }, {
        # episode
        'url': 'https://www.southpark.de/folgen/242csn/south-park-her-mit-dem-hirn-staffel-1-ep-7',
        'info_dict': {
            'id': '607115f3-496f-40c3-8647-2b0bcff486c0',
            'ext': 'mp4',
            'title': 'South Park | Pink Eye | E 0107 | HDSS0107X deu | Version: 634312 | Comedy Central S1',
        },
    }]

    def _get_feed_query(self, uri):
        return {
            'accountOverride': 'intl.mtvi.com',
            'arcEp': 'shared.southpark.gsa.de',
            'ep': '50c78199',
            'imageEp': 'shared.southpark.gsa.de',
            'clusterName': 'EMEAA',
            'mgid': uri,
        }


class SouthParkDeEnIE(SouthParkIE):
    IE_NAME = 'southpark.de:en'
    _VALID_URL = r'https?://(?:www\.)?(?P<url>southpark\.de/en/(?:video-clips|episodes|collections)/(?P<id>.+?)(\?|#|$))'
    _FEED_URL = 'http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed'

    _TESTS = [{
        # clip
        'url': 'https://www.southpark.de/en/video-clips/ct46op/south-park-tooth-fairy-cartman',
        'info_dict': {
            'id': 'e99d45ea-ed00-11e0-aca6-0026b9414f30',
            'ext': 'mp4',
            'title': 'Tooth Fairy Cartman',
            'description': 'Cartman dresses up as the Tooth Fairy to steal Butters\' tooth from underneath his pillow. Cartman gets $4 for this tooth, feeding the drive for more teeth.',
        },
    }, {
        # episode
        'url': 'https://www.southpark.de/en/episodes/yy0vjs/south-park-the-pandemic-special-season-24-ep-1',
        'info_dict': {
            'id': 'f5fbd823-04bc-11eb-9b1b-0e40cf2fc285',
            'ext': 'mp4',
            'title': 'South Park',
            'description': 'Randy comes to terms with his role in the COVID-19 outbreak as the on-going pandemic presents continued challenges to the citizens of South Park.',
        },
    }]

    def _get_feed_query(self, uri):
        return {
            'accountOverride': 'intl.mtvi.com',
            'arcEp': 'shared.southpark.gsa.en',
            'ep': '20476225',
            'imageEp': 'shared.southpark.gsa.en',
            'clusterName': 'EMEAA',
            'mgid': uri,
        }


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

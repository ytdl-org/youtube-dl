from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .theplatform import ThePlatformIE
from ..utils import (
    find_xpath_attr,
    lowercase_escape,
    smuggle_url,
    unescapeHTML,
)


class NBCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nbc\.com/(?:[^/]+/)+(?P<id>n?\d+)'

    _TESTS = [
        {
            'url': 'http://www.nbc.com/the-tonight-show/segments/112966',
            'info_dict': {
                'id': '112966',
                'ext': 'mp4',
                'title': 'Jimmy Fallon Surprises Fans at Ben & Jerry\'s',
                'description': 'Jimmy gives out free scoops of his new "Tonight Dough" ice cream flavor by surprising customers at the Ben & Jerry\'s scoop shop.',
                'timestamp': 1424246400,
                'upload_date': '20150218',
                'uploader': 'NBCU-COM',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.nbc.com/the-tonight-show/episodes/176',
            'info_dict': {
                'id': '176',
                'ext': 'flv',
                'title': 'Ricky Gervais, Steven Van Zandt, ILoveMakonnen',
                'description': 'A brand new episode of The Tonight Show welcomes Ricky Gervais, Steven Van Zandt and ILoveMakonnen.',
            },
            'skip': '404 Not Found',
        },
        {
            'url': 'http://www.nbc.com/saturday-night-live/video/star-wars-teaser/2832821',
            'info_dict': {
                'id': '2832821',
                'ext': 'mp4',
                'title': 'Star Wars Teaser',
                'description': 'md5:0b40f9cbde5b671a7ff62fceccc4f442',
                'timestamp': 1417852800,
                'upload_date': '20141206',
                'uploader': 'NBCU-COM',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
            'skip': 'Only works from US',
        },
        {
            # This video has expired but with an escaped embedURL
            'url': 'http://www.nbc.com/parenthood/episode-guide/season-5/just-like-at-home/515',
            'only_matching': True,
        },
        {
            # HLS streams requires the 'hdnea3' cookie
            'url': 'http://www.nbc.com/Kings/video/goliath/n1806',
            'info_dict': {
                'id': 'n1806',
                'ext': 'mp4',
                'title': 'Goliath',
                'description': 'When an unknown soldier saves the life of the King\'s son in battle, he\'s thrust into the limelight and politics of the kingdom.',
                'timestamp': 1237100400,
                'upload_date': '20090315',
                'uploader': 'NBCU-COM',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Only works from US',
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        theplatform_url = unescapeHTML(lowercase_escape(self._html_search_regex(
            [
                r'(?:class="video-player video-player-full" data-mpx-url|class="player" src)="(.*?)"',
                r'<iframe[^>]+src="((?:https?:)?//player\.theplatform\.com/[^"]+)"',
                r'"embedURL"\s*:\s*"([^"]+)"'
            ],
            webpage, 'theplatform url').replace('_no_endcard', '').replace('\\/', '/')))
        if theplatform_url.startswith('//'):
            theplatform_url = 'http:' + theplatform_url
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(theplatform_url, {'source_url': url}),
            'id': video_id,
        }


class NBCSportsVPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://vplayer\.nbcsports\.com/(?:[^/]+/)+(?P<id>[0-9a-zA-Z_]+)'

    _TESTS = [{
        'url': 'https://vplayer.nbcsports.com/p/BxmELC/nbcsports_share/select/9CsDKds0kvHI',
        'info_dict': {
            'id': '9CsDKds0kvHI',
            'ext': 'flv',
            'description': 'md5:df390f70a9ba7c95ff1daace988f0d8d',
            'title': 'Tyler Kalinoski hits buzzer-beater to lift Davidson',
            'timestamp': 1426270238,
            'upload_date': '20150313',
            'uploader': 'NBCU-SPORTS',
        }
    }, {
        'url': 'http://vplayer.nbcsports.com/p/BxmELC/nbc_embedshare/select/_hqLjQ95yx8Z',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        iframe_m = re.search(
            r'<iframe[^>]+src="(?P<url>https?://vplayer\.nbcsports\.com/[^"]+)"', webpage)
        if iframe_m:
            return iframe_m.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        theplatform_url = self._og_search_video_url(webpage)
        return self.url_result(theplatform_url, 'ThePlatform')


class NBCSportsIE(InfoExtractor):
    # Does not include https because its certificate is invalid
    _VALID_URL = r'https?://(?:www\.)?nbcsports\.com//?(?:[^/]+/)+(?P<id>[0-9a-z-]+)'

    _TEST = {
        'url': 'http://www.nbcsports.com//college-basketball/ncaab/tom-izzo-michigan-st-has-so-much-respect-duke',
        'info_dict': {
            'id': 'PHJSaFWbrTY9',
            'ext': 'flv',
            'title': 'Tom Izzo, Michigan St. has \'so much respect\' for Duke',
            'description': 'md5:ecb459c9d59e0766ac9c7d5d0eda8113',
            'uploader': 'NBCU-SPORTS',
            'upload_date': '20150330',
            'timestamp': 1427726529,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return self.url_result(
            NBCSportsVPlayerIE._extract_url(webpage), 'NBCSportsVPlayer')


class CSNNEIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?csnne\.com/video/(?P<id>[0-9a-z-]+)'

    _TEST = {
        'url': 'http://www.csnne.com/video/snc-evening-update-wright-named-red-sox-no-5-starter',
        'info_dict': {
            'id': 'yvBLLUgQ8WU0',
            'ext': 'mp4',
            'title': 'SNC evening update: Wright named Red Sox\' No. 5 starter.',
            'description': 'md5:1753cfee40d9352b19b4c9b3e589b9e3',
            'timestamp': 1459369979,
            'upload_date': '20160330',
            'uploader': 'NBCU-SPORTS',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': self._html_search_meta('twitter:player:stream', webpage),
            'display_id': display_id,
        }


class NBCNewsIE(ThePlatformIE):
    _VALID_URL = r'''(?x)https?://(?:www\.)?(?:nbcnews|today|msnbc)\.com/
        (?:video/.+?/(?P<id>\d+)|
        ([^/]+/)*(?:.*-)?(?P<mpx_id>[^/?]+))
        '''

    _TESTS = [
        {
            'url': 'http://www.nbcnews.com/video/nbc-news/52753292',
            'md5': '47abaac93c6eaf9ad37ee6c4463a5179',
            'info_dict': {
                'id': '52753292',
                'ext': 'flv',
                'title': 'Crew emerges after four-month Mars food study',
                'description': 'md5:24e632ffac72b35f8b67a12d1b6ddfc1',
            },
        },
        {
            'url': 'http://www.nbcnews.com/watch/nbcnews-com/how-twitter-reacted-to-the-snowden-interview-269389891880',
            'md5': 'af1adfa51312291a017720403826bb64',
            'info_dict': {
                'id': '269389891880',
                'ext': 'mp4',
                'title': 'How Twitter Reacted To The Snowden Interview',
                'description': 'md5:65a0bd5d76fe114f3c2727aa3a81fe64',
                'uploader': 'NBCU-NEWS',
                'timestamp': 1401363060,
                'upload_date': '20140529',
            },
        },
        {
            'url': 'http://www.nbcnews.com/feature/dateline-full-episodes/full-episode-family-business-n285156',
            'md5': 'fdbf39ab73a72df5896b6234ff98518a',
            'info_dict': {
                'id': '529953347624',
                'ext': 'mp4',
                'title': 'FULL EPISODE: Family Business',
                'description': 'md5:757988edbaae9d7be1d585eb5d55cc04',
            },
            'skip': 'This page is unavailable.',
        },
        {
            'url': 'http://www.nbcnews.com/nightly-news/video/nightly-news-with-brian-williams-full-broadcast-february-4-394064451844',
            'md5': '73135a2e0ef819107bbb55a5a9b2a802',
            'info_dict': {
                'id': '394064451844',
                'ext': 'mp4',
                'title': 'Nightly News with Brian Williams Full Broadcast (February 4)',
                'description': 'md5:1c10c1eccbe84a26e5debb4381e2d3c5',
                'timestamp': 1423104900,
                'uploader': 'NBCU-NEWS',
                'upload_date': '20150205',
            },
        },
        {
            'url': 'http://www.nbcnews.com/business/autos/volkswagen-11-million-vehicles-could-have-suspect-software-emissions-scandal-n431456',
            'md5': 'a49e173825e5fcd15c13fc297fced39d',
            'info_dict': {
                'id': '529953347624',
                'ext': 'mp4',
                'title': 'Volkswagen U.S. Chief:\xa0 We Have Totally Screwed Up',
                'description': 'md5:c8be487b2d80ff0594c005add88d8351',
                'upload_date': '20150922',
                'timestamp': 1442917800,
                'uploader': 'NBCU-NEWS',
            },
        },
        {
            'url': 'http://www.today.com/video/see-the-aurora-borealis-from-space-in-stunning-new-nasa-video-669831235788',
            'md5': '118d7ca3f0bea6534f119c68ef539f71',
            'info_dict': {
                'id': '669831235788',
                'ext': 'mp4',
                'title': 'See the aurora borealis from space in stunning new NASA video',
                'description': 'md5:74752b7358afb99939c5f8bb2d1d04b1',
                'upload_date': '20160420',
                'timestamp': 1461152093,
                'uploader': 'NBCU-NEWS',
            },
        },
        {
            'url': 'http://www.msnbc.com/all-in-with-chris-hayes/watch/the-chaotic-gop-immigration-vote-314487875924',
            'md5': '6d236bf4f3dddc226633ce6e2c3f814d',
            'info_dict': {
                'id': '314487875924',
                'ext': 'mp4',
                'title': 'The chaotic GOP immigration vote',
                'description': 'The Republican House votes on a border bill that has no chance of getting through the Senate or signed by the President and is drawing criticism from all sides.',
                'thumbnail': 're:^https?://.*\.jpg$',
                'timestamp': 1406937606,
                'upload_date': '20140802',
                'uploader': 'NBCU-NEWS',
                'categories': ['MSNBC/Topics/Franchise/Best of last night', 'MSNBC/Topics/General/Congress'],
            },
        },
        {
            'url': 'http://www.nbcnews.com/watch/dateline/full-episode--deadly-betrayal-386250819952',
            'only_matching': True,
        },
        {
            # From http://www.vulture.com/2016/06/letterman-couldnt-care-less-about-late-night.html
            'url': 'http://www.nbcnews.com/widget/video-embed/701714499682',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        if video_id is not None:
            all_info = self._download_xml('http://www.nbcnews.com/id/%s/displaymode/1219' % video_id, video_id)
            info = all_info.find('video')

            return {
                'id': video_id,
                'title': info.find('headline').text,
                'ext': 'flv',
                'url': find_xpath_attr(info, 'media', 'type', 'flashVideo').text,
                'description': info.find('caption').text,
                'thumbnail': find_xpath_attr(info, 'media', 'type', 'thumbnail').text,
            }
        else:
            # "feature" and "nightly-news" pages use theplatform.com
            video_id = mobj.group('mpx_id')
            if not video_id.isdigit():
                webpage = self._download_webpage(url, video_id)
                info = None
                bootstrap_json = self._search_regex(
                    [r'(?m)(?:var\s+(?:bootstrapJson|playlistData)|NEWS\.videoObj)\s*=\s*({.+});?\s*$',
                     r'videoObj\s*:\s*({.+})', r'data-video="([^"]+)"'],
                    webpage, 'bootstrap json', default=None)
                bootstrap = self._parse_json(
                    bootstrap_json, video_id, transform_source=unescapeHTML)
                if 'results' in bootstrap:
                    info = bootstrap['results'][0]['video']
                elif 'video' in bootstrap:
                    info = bootstrap['video']
                else:
                    info = bootstrap
                video_id = info['mpxId']

            return {
                '_type': 'url_transparent',
                'id': video_id,
                # http://feed.theplatform.com/f/2E2eJC/nbcnews also works
                'url': 'http://feed.theplatform.com/f/2E2eJC/nnd_NBCNews?byId=%s' % video_id,
                'ie_key': 'ThePlatformFeed',
            }


class NBCOlympicsIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nbcolympics\.com/video/(?P<id>[a-z-]+)'

    _TEST = {
        # Geo-restricted to US
        'url': 'http://www.nbcolympics.com/video/justin-roses-son-leo-was-tears-after-his-dad-won-gold',
        'md5': '54fecf846d05429fbaa18af557ee523a',
        'info_dict': {
            'id': 'WjTBzDXx5AUq',
            'display_id': 'justin-roses-son-leo-was-tears-after-his-dad-won-gold',
            'ext': 'mp4',
            'title': 'Rose\'s son Leo was in tears after his dad won gold',
            'description': 'Olympic gold medalist Justin Rose gets emotional talking to the impact his win in men\'s golf has already had on his children.',
            'timestamp': 1471274964,
            'upload_date': '20160815',
            'uploader': 'NBCU-SPORTS',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        drupal_settings = self._parse_json(self._search_regex(
            r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
            webpage, 'drupal settings'), display_id)

        iframe_url = drupal_settings['vod']['iframe_url']
        theplatform_url = iframe_url.replace(
            'vplayer.nbcolympics.com', 'player.theplatform.com')

        return {
            '_type': 'url_transparent',
            'url': theplatform_url,
            'ie_key': ThePlatformIE.ie_key(),
            'display_id': display_id,
        }

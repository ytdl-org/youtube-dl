from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_HTTPError,
)
from ..utils import (
    ExtractorError,
    find_xpath_attr,
    lowercase_escape,
    unescapeHTML,
)


class NBCIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nbc\.com/(?:[^/]+/)+(?P<id>n?\d+)'

    _TESTS = [
        {
            'url': 'http://www.nbc.com/the-tonight-show/segments/112966',
            # md5 checksum is not stable
            'info_dict': {
                'id': 'c9xnCo0YPOPH',
                'ext': 'flv',
                'title': 'Jimmy Fallon Surprises Fans at Ben & Jerry\'s',
                'description': 'Jimmy gives out free scoops of his new "Tonight Dough" ice cream flavor by surprising customers at the Ben & Jerry\'s scoop shop.',
            },
        },
        {
            'url': 'http://www.nbc.com/the-tonight-show/episodes/176',
            'info_dict': {
                'id': 'XwU9KZkp98TH',
                'ext': 'flv',
                'title': 'Ricky Gervais, Steven Van Zandt, ILoveMakonnen',
                'description': 'A brand new episode of The Tonight Show welcomes Ricky Gervais, Steven Van Zandt and ILoveMakonnen.',
            },
            'skip': 'Only works from US',
        },
        {
            'url': 'http://www.nbc.com/saturday-night-live/video/star-wars-teaser/2832821',
            'info_dict': {
                'id': '8iUuyzWDdYUZ',
                'ext': 'flv',
                'title': 'Star Wars Teaser',
                'description': 'md5:0b40f9cbde5b671a7ff62fceccc4f442',
            },
            'skip': 'Only works from US',
        },
        {
            # This video has expired but with an escaped embedURL
            'url': 'http://www.nbc.com/parenthood/episode-guide/season-5/just-like-at-home/515',
            'skip': 'Expired'
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        theplatform_url = unescapeHTML(lowercase_escape(self._html_search_regex(
            [
                r'(?:class="video-player video-player-full" data-mpx-url|class="player" src)="(.*?)"',
                r'"embedURL"\s*:\s*"([^"]+)"'
            ],
            webpage, 'theplatform url').replace('_no_endcard', '').replace('\\/', '/')))
        if theplatform_url.startswith('//'):
            theplatform_url = 'http:' + theplatform_url
        return self.url_result(theplatform_url)


class NBCSportsVPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://vplayer\.nbcsports\.com/(?:[^/]+/)+(?P<id>[0-9a-zA-Z_]+)'

    _TESTS = [{
        'url': 'https://vplayer.nbcsports.com/p/BxmELC/nbcsports_share/select/9CsDKds0kvHI',
        'info_dict': {
            'id': '9CsDKds0kvHI',
            'ext': 'flv',
            'description': 'md5:df390f70a9ba7c95ff1daace988f0d8d',
            'title': 'Tyler Kalinoski hits buzzer-beater to lift Davidson',
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
    # Does not include https becuase its certificate is invalid
    _VALID_URL = r'http://www\.nbcsports\.com//?(?:[^/]+/)+(?P<id>[0-9a-z-]+)'

    _TEST = {
        'url': 'http://www.nbcsports.com//college-basketball/ncaab/tom-izzo-michigan-st-has-so-much-respect-duke',
        'info_dict': {
            'id': 'PHJSaFWbrTY9',
            'ext': 'flv',
            'title': 'Tom Izzo, Michigan St. has \'so much respect\' for Duke',
            'description': 'md5:ecb459c9d59e0766ac9c7d5d0eda8113',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return self.url_result(
            NBCSportsVPlayerIE._extract_url(webpage), 'NBCSportsVPlayer')


class NBCNewsIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?nbcnews\.com/
        (?:video/.+?/(?P<id>\d+)|
        (?:watch|feature|nightly-news)/[^/]+/(?P<title>.+))
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
            'url': 'http://www.nbcnews.com/feature/edward-snowden-interview/how-twitter-reacted-snowden-interview-n117236',
            'md5': 'b2421750c9f260783721d898f4c42063',
            'info_dict': {
                'id': 'I1wpAI_zmhsQ',
                'ext': 'mp4',
                'title': 'How Twitter Reacted To The Snowden Interview',
                'description': 'md5:65a0bd5d76fe114f3c2727aa3a81fe64',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://www.nbcnews.com/feature/dateline-full-episodes/full-episode-family-business-n285156',
            'md5': 'fdbf39ab73a72df5896b6234ff98518a',
            'info_dict': {
                'id': 'Wjf9EDR3A_60',
                'ext': 'mp4',
                'title': 'FULL EPISODE: Family Business',
                'description': 'md5:757988edbaae9d7be1d585eb5d55cc04',
            },
        },
        {
            'url': 'http://www.nbcnews.com/nightly-news/video/nightly-news-with-brian-williams-full-broadcast-february-4-394064451844',
            'md5': 'b5dda8cddd8650baa0dcb616dd2cf60d',
            'info_dict': {
                'id': 'sekXqyTVnmN3',
                'ext': 'mp4',
                'title': 'Nightly News with Brian Williams Full Broadcast (February 4)',
                'description': 'md5:1c10c1eccbe84a26e5debb4381e2d3c5',
            },
        },
        {
            'url': 'http://www.nbcnews.com/watch/dateline/full-episode--deadly-betrayal-386250819952',
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
                'description': compat_str(info.find('caption').text),
                'thumbnail': find_xpath_attr(info, 'media', 'type', 'thumbnail').text,
            }
        else:
            # "feature" and "nightly-news" pages use theplatform.com
            title = mobj.group('title')
            webpage = self._download_webpage(url, title)
            bootstrap_json = self._search_regex(
                r'var\s+(?:bootstrapJson|playlistData)\s*=\s*({.+});?\s*$',
                webpage, 'bootstrap json', flags=re.MULTILINE)
            bootstrap = self._parse_json(bootstrap_json, video_id)
            info = bootstrap['results'][0]['video']
            mpxid = info['mpxId']

            base_urls = [
                info['fallbackPlaylistUrl'],
                info['associatedPlaylistUrl'],
            ]

            for base_url in base_urls:
                if not base_url:
                    continue
                playlist_url = base_url + '?form=MPXNBCNewsAPI'

                try:
                    all_videos = self._download_json(playlist_url, title)
                except ExtractorError as ee:
                    if isinstance(ee.cause, compat_HTTPError):
                        continue
                    raise

                if not all_videos or 'videos' not in all_videos:
                    continue

                try:
                    info = next(v for v in all_videos['videos'] if v['mpxId'] == mpxid)
                    break
                except StopIteration:
                    continue

            if info is None:
                raise ExtractorError('Could not find video in playlists')

            return {
                '_type': 'url',
                # We get the best quality video
                'url': info['videoAssets'][-1]['publicUrl'],
                'ie_key': 'ThePlatform',
            }


class MSNBCIE(InfoExtractor):
    # https URLs redirect to corresponding http ones
    _VALID_URL = r'http://www\.msnbc\.com/[^/]+/watch/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.msnbc.com/all-in-with-chris-hayes/watch/the-chaotic-gop-immigration-vote-314487875924',
        'md5': '6d236bf4f3dddc226633ce6e2c3f814d',
        'info_dict': {
            'id': 'n_hayes_Aimm_140801_272214',
            'ext': 'mp4',
            'title': 'The chaotic GOP immigration vote',
            'description': 'The Republican House votes on a border bill that has no chance of getting through the Senate or signed by the President and is drawing criticism from all sides.',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1406937606,
            'upload_date': '20140802',
            'categories': ['MSNBC/Topics/Franchise/Best of last night', 'MSNBC/Topics/General/Congress'],
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        embed_url = self._html_search_meta('embedURL', webpage)
        return self.url_result(embed_url)

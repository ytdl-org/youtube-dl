from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .theplatform import ThePlatformIE
from ..utils import (
    find_xpath_attr,
    lowercase_escape,
    smuggle_url,
    unescapeHTML,
    update_url_query,
    int_or_none,
    HEADRequest,
    parse_iso8601,
)


class NBCIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nbc\.com/(?:[^/]+/)+(?P<id>n?\d+)'

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
    _VALID_URL = r'https?://www\.nbcsports\.com//?(?:[^/]+/)+(?P<id>[0-9a-z-]+)'

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
    _VALID_URL = r'https?://www\.csnne\.com/video/(?P<id>[0-9a-z-]+)'

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
    _VALID_URL = r'''(?x)https?://(?:www\.)?(?:nbcnews|today)\.com/
        (?:video/.+?/(?P<id>\d+)|
        ([^/]+/)*(?P<display_id>[^/?]+))
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
            },
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
            },
        },
        {
            'url': 'http://www.nbcnews.com/business/autos/volkswagen-11-million-vehicles-could-have-suspect-software-emissions-scandal-n431456',
            'md5': 'a49e173825e5fcd15c13fc297fced39d',
            'info_dict': {
                'id': '529953347624',
                'ext': 'mp4',
                'title': 'Volkswagen U.S. Chief: We \'Totally Screwed Up\'',
                'description': 'md5:d22d1281a24f22ea0880741bb4dd6301',
            },
            'expected_warnings': ['http-6000 is not available']
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
                'description': info.find('caption').text,
                'thumbnail': find_xpath_attr(info, 'media', 'type', 'thumbnail').text,
            }
        else:
            # "feature" and "nightly-news" pages use theplatform.com
            display_id = mobj.group('display_id')
            webpage = self._download_webpage(url, display_id)
            info = None
            bootstrap_json = self._search_regex(
                r'(?m)var\s+(?:bootstrapJson|playlistData)\s*=\s*({.+});?\s*$',
                webpage, 'bootstrap json', default=None)
            if bootstrap_json:
                bootstrap = self._parse_json(bootstrap_json, display_id)
                info = bootstrap['results'][0]['video']
            else:
                player_instance_json = self._search_regex(
                    r'videoObj\s*:\s*({.+})', webpage, 'player instance', default=None)
                if not player_instance_json:
                    player_instance_json = self._html_search_regex(
                        r'data-video="([^"]+)"', webpage, 'video json')
                info = self._parse_json(player_instance_json, display_id)
            video_id = info['mpxId']
            title = info['title']

            subtitles = {}
            caption_links = info.get('captionLinks')
            if caption_links:
                for (sub_key, sub_ext) in (('smpte-tt', 'ttml'), ('web-vtt', 'vtt'), ('srt', 'srt')):
                    sub_url = caption_links.get(sub_key)
                    if sub_url:
                        subtitles.setdefault('en', []).append({
                            'url': sub_url,
                            'ext': sub_ext,
                        })

            formats = []
            for video_asset in info['videoAssets']:
                video_url = video_asset.get('publicUrl')
                if not video_url:
                    continue
                container = video_asset.get('format')
                asset_type = video_asset.get('assetType') or ''
                if container == 'ISM' or asset_type == 'FireTV-Once':
                    continue
                elif asset_type == 'OnceURL':
                    tp_formats, tp_subtitles = self._extract_theplatform_smil(
                        video_url, video_id)
                    formats.extend(tp_formats)
                    subtitles = self._merge_subtitles(subtitles, tp_subtitles)
                else:
                    tbr = int_or_none(video_asset.get('bitRate') or video_asset.get('bitrate'), 1000)
                    format_id = 'http%s' % ('-%d' % tbr if tbr else '')
                    video_url = update_url_query(
                        video_url, {'format': 'redirect'})
                    # resolve the url so that we can check availability and detect the correct extension
                    head = self._request_webpage(
                        HEADRequest(video_url), video_id,
                        'Checking %s url' % format_id,
                        '%s is not available' % format_id,
                        fatal=False)
                    if head:
                        video_url = head.geturl()
                        formats.append({
                            'format_id': format_id,
                            'url': video_url,
                            'width': int_or_none(video_asset.get('width')),
                            'height': int_or_none(video_asset.get('height')),
                            'tbr': tbr,
                            'container': video_asset.get('format'),
                        })
            self._sort_formats(formats)

            return {
                'id': video_id,
                'title': title,
                'description': info.get('description'),
                'thumbnail': info.get('thumbnail'),
                'duration': int_or_none(info.get('duration')),
                'timestamp': parse_iso8601(info.get('pubDate') or info.get('pub_date')),
                'formats': formats,
                'subtitles': subtitles,
            }


class MSNBCIE(InfoExtractor):
    # https URLs redirect to corresponding http ones
    _VALID_URL = r'https?://www\.msnbc\.com/[^/]+/watch/(?P<id>[^/]+)'
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
            'uploader': 'NBCU-NEWS',
            'categories': ['MSNBC/Topics/Franchise/Best of last night', 'MSNBC/Topics/General/Congress'],
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        embed_url = self._html_search_meta('embedURL', webpage)
        return self.url_result(embed_url)

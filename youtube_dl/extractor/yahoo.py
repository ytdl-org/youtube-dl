# coding: utf-8
from __future__ import unicode_literals

import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urlparse,
    clean_html,
    int_or_none,
)


class YahooIE(InfoExtractor):
    IE_DESC = 'Yahoo screen and movies'
    _VALID_URL = r'(?P<url>(?P<host>https?://(?:[a-zA-Z]{2}\.)?[\da-zA-Z_-]+\.yahoo\.com)/(?:[^/]+/)*(?P<display_id>.+?)-(?P<id>[0-9]+)(?:-[a-z]+)?\.html)'
    _TESTS = [
        {
            'url': 'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
            'md5': '4962b075c08be8690a922ee026d05e69',
            'info_dict': {
                'id': '2d25e626-2378-391f-ada0-ddaf1417e588',
                'ext': 'mp4',
                'title': 'Julian Smith & Travis Legg Watch Julian Smith',
                'description': 'Julian and Travis watch Julian Smith',
                'duration': 6863,
            },
        },
        {
            'url': 'http://screen.yahoo.com/wired/codefellas-s1-ep12-cougar-lies-103000935.html',
            'md5': 'd6e6fc6e1313c608f316ddad7b82b306',
            'info_dict': {
                'id': 'd1dedf8c-d58c-38c3-8963-e899929ae0a9',
                'ext': 'mp4',
                'title': 'Codefellas - The Cougar Lies with Spanish Moss',
                'description': 'md5:66b627ab0a282b26352136ca96ce73c1',
                'duration': 151,
            },
        },
        {
            'url': 'https://screen.yahoo.com/community/community-sizzle-reel-203225340.html?format=embed',
            'md5': '60e8ac193d8fb71997caa8fce54c6460',
            'info_dict': {
                'id': '4fe78544-8d48-39d8-97cd-13f205d9fcdb',
                'ext': 'mp4',
                'title': "Yahoo Saves 'Community'",
                'description': 'md5:4d4145af2fd3de00cbb6c1d664105053',
                'duration': 170,
            }
        },
        {
            'url': 'https://tw.screen.yahoo.com/taipei-opinion-poll/選情站報-街頭民調-台北市篇-102823042.html',
            'md5': '92a7fdd8a08783c68a174d7aa067dde8',
            'info_dict': {
                'id': '7a23b569-7bea-36cb-85b9-bd5301a0a1fb',
                'ext': 'mp4',
                'title': '選情站報 街頭民調 台北市篇',
                'description': '選情站報 街頭民調 台北市篇',
                'duration': 429,
            }
        },
        {
            'url': 'https://uk.screen.yahoo.com/editor-picks/cute-raccoon-freed-drain-using-091756545.html',
            'md5': '0b51660361f0e27c9789e7037ef76f4b',
            'info_dict': {
                'id': 'b3affa53-2e14-3590-852b-0e0db6cd1a58',
                'ext': 'mp4',
                'title': 'Cute Raccoon Freed From Drain\u00a0Using Angle Grinder',
                'description': 'md5:f66c890e1490f4910a9953c941dee944',
                'duration': 97,
            }
        },
        {
            'url': 'https://ca.sports.yahoo.com/video/program-makes-hockey-more-affordable-013127711.html',
            'md5': '57e06440778b1828a6079d2f744212c4',
            'info_dict': {
                'id': 'c9fa2a36-0d4d-3937-b8f6-cc0fb1881e73',
                'ext': 'mp4',
                'title': 'Program that makes hockey more affordable not offered in Manitoba',
                'description': 'md5:c54a609f4c078d92b74ffb9bf1f496f4',
                'duration': 121,
            }
        }, {
            'url': 'https://ca.finance.yahoo.com/news/20-most-valuable-brands-world-112600775.html',
            'md5': '3e401e4eed6325aa29d9b96125fd5b4f',
            'info_dict': {
                'id': 'c1b4c09c-8ed8-3b65-8b05-169c55358a83',
                'ext': 'mp4',
                'title': "Apple Is The World's Most Valuable Brand",
                'description': 'md5:73eabc1a11c6f59752593b2ceefa1262',
                'duration': 21,
            }
        }, {
            'url': 'http://news.yahoo.com/video/china-moses-crazy-blues-104538833.html',
            'md5': '67010fdf3a08d290e060a4dd96baa07b',
            'info_dict': {
                'id': 'f885cf7f-43d4-3450-9fac-46ac30ece521',
                'ext': 'mp4',
                'title': 'China Moses Is Crazy About the Blues',
                'description': 'md5:9900ab8cd5808175c7b3fe55b979bed0',
                'duration': 128,
            }
        }, {
            'url': 'https://in.lifestyle.yahoo.com/video/connect-dots-dark-side-virgo-090247395.html',
            'md5': 'd9a083ccf1379127bf25699d67e4791b',
            'info_dict': {
                'id': '52aeeaa3-b3d1-30d8-9ef8-5d0cf05efb7c',
                'ext': 'mp4',
                'title': 'Connect the Dots: Dark Side of Virgo',
                'description': 'md5:1428185051cfd1949807ad4ff6d3686a',
                'duration': 201,
            }
        }, {
            'url': 'https://gma.yahoo.com/pizza-delivery-man-surprised-huge-tip-college-kids-195200785.html',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        url = mobj.group('url')
        host = mobj.group('host')
        webpage = self._download_webpage(url, display_id)

        # Look for iframed media first
        iframe_m = re.search(r'<iframe[^>]+src="(/video/.+?-\d+\.html\?format=embed.*?)"', webpage)
        if iframe_m:
            iframepage = self._download_webpage(
                host + iframe_m.group(1), display_id, 'Downloading iframe webpage')
            items_json = self._search_regex(
                r'mediaItems: (\[.+?\])$', iframepage, 'items', flags=re.MULTILINE, default=None)
            if items_json:
                items = json.loads(items_json)
                video_id = items[0]['id']
                return self._get_info(video_id, display_id, webpage)

        items_json = self._search_regex(
            r'mediaItems: ({.*?})$', webpage, 'items', flags=re.MULTILINE,
            default=None)
        if items_json is None:
            CONTENT_ID_REGEXES = [
                r'YUI\.namespace\("Media"\)\.CONTENT_ID\s*=\s*"([^"]+)"',
                r'root\.App\.Cache\.context\.videoCache\.curVideo = \{"([^"]+)"',
                r'"first_videoid"\s*:\s*"([^"]+)"',
            ]
            video_id = self._search_regex(CONTENT_ID_REGEXES, webpage, 'content ID')
        else:
            items = json.loads(items_json)
            info = items['mediaItems']['query']['results']['mediaObj'][0]
            # The 'meta' field is not always in the video webpage, we request it
            # from another page
            video_id = info['id']
        return self._get_info(video_id, display_id, webpage)

    def _get_info(self, video_id, display_id, webpage):
        region = self._search_regex(
            r'\\?"region\\?"\s*:\s*\\?"([^"]+?)\\?"',
            webpage, 'region', fatal=False, default='US')
        query = ('SELECT * FROM yahoo.media.video.streams WHERE id="%s"'
                 ' AND plrs="86Gj0vCaSzV_Iuf6hNylf2" AND region="%s"'
                 ' AND protocol="http"' % (video_id, region))
        data = compat_urllib_parse.urlencode({
            'q': query,
            'env': 'prod',
            'format': 'json',
        })
        query_result = self._download_json(
            'http://video.query.yahoo.com/v1/public/yql?' + data,
            display_id, 'Downloading video info')

        info = query_result['query']['results']['mediaObj'][0]
        meta = info.get('meta')

        if not meta:
            msg = info['status'].get('msg')
            if msg:
                raise ExtractorError(
                    '%s returned error: %s' % (self.IE_NAME, msg), expected=True)
            raise ExtractorError('Unable to extract media object meta')

        formats = []
        for s in info['streams']:
            format_info = {
                'width': int_or_none(s.get('width')),
                'height': int_or_none(s.get('height')),
                'tbr': int_or_none(s.get('bitrate')),
            }

            host = s['host']
            path = s['path']
            if host.startswith('rtmp'):
                format_info.update({
                    'url': host,
                    'play_path': path,
                    'ext': 'flv',
                })
            else:
                format_url = compat_urlparse.urljoin(host, path)
                format_info['url'] = format_url
            formats.append(format_info)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': meta['title'],
            'formats': formats,
            'description': clean_html(meta['description']),
            'thumbnail': meta['thumbnail'] if meta.get('thumbnail') else self._og_search_thumbnail(webpage),
            'duration': int_or_none(meta.get('duration')),
        }


class YahooSearchIE(SearchInfoExtractor):
    IE_DESC = 'Yahoo screen search'
    _MAX_RESULTS = 1000
    IE_NAME = 'screen.yahoo:search'
    _SEARCH_KEY = 'yvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        entries = []
        for pagenum in itertools.count(0):
            result_url = 'http://video.search.yahoo.com/search/?p=%s&fr=screen&o=js&gs=0&b=%d' % (compat_urllib_parse.quote_plus(query), pagenum * 30)
            info = self._download_json(result_url, query,
                                       note='Downloading results page ' + str(pagenum + 1))
            m = info['m']
            results = info['results']

            for (i, r) in enumerate(results):
                if (pagenum * 30) + i >= n:
                    break
                mobj = re.search(r'(?P<url>screen\.yahoo\.com/.*?-\d*?\.html)"', r)
                e = self.url_result('http://' + mobj.group('url'), 'Yahoo')
                entries.append(e)
            if (pagenum * 30 + i >= n) or (m['last'] >= (m['total'] - 1)):
                break

        return {
            '_type': 'playlist',
            'id': query,
            'entries': entries,
        }

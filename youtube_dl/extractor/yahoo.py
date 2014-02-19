from __future__ import unicode_literals

import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urlparse,
    clean_html,
    int_or_none,
)


class YahooIE(InfoExtractor):
    IE_DESC = 'Yahoo screen'
    _VALID_URL = r'http://screen\.yahoo\.com/.*?-(?P<id>\d*?)\.html'
    _TESTS = [
        {
            'url': 'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
            'file': '214727115.mp4',
            'md5': '4962b075c08be8690a922ee026d05e69',
            'info_dict': {
                'title': 'Julian Smith & Travis Legg Watch Julian Smith',
                'description': 'Julian and Travis watch Julian Smith',
            },
        },
        {
            'url': 'http://screen.yahoo.com/wired/codefellas-s1-ep12-cougar-lies-103000935.html',
            'file': '103000935.mp4',
            'md5': 'd6e6fc6e1313c608f316ddad7b82b306',
            'info_dict': {
                'title': 'Codefellas - The Cougar Lies with Spanish Moss',
                'description': 'Agent Topple\'s mustache does its dirty work, and Nicole brokers a deal for peace. But why is the NSA collecting millions of Instagram brunch photos? And if your waffles have nothing to hide, what are they so worried about?',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        items_json = self._search_regex(r'mediaItems: ({.*?})$',
            webpage, 'items', flags=re.MULTILINE)
        items = json.loads(items_json)
        info = items['mediaItems']['query']['results']['mediaObj'][0]
        # The 'meta' field is not always in the video webpage, we request it
        # from another page
        long_id = info['id']
        return self._get_info(long_id, video_id)

    def _get_info(self, long_id, video_id):
        query = ('SELECT * FROM yahoo.media.video.streams WHERE id="%s"'
                 ' AND plrs="86Gj0vCaSzV_Iuf6hNylf2" AND region="US"'
                 ' AND protocol="http"' % long_id)
        data = compat_urllib_parse.urlencode({
            'q': query,
            'env': 'prod',
            'format': 'json',
        })
        query_result_json = self._download_webpage(
            'http://video.query.yahoo.com/v1/public/yql?' + data,
            video_id, 'Downloading video info')
        query_result = json.loads(query_result_json)
        info = query_result['query']['results']['mediaObj'][0]
        meta = info['meta']

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
            'title': meta['title'],
            'formats': formats,
            'description': clean_html(meta['description']),
            'thumbnail': meta['thumbnail'],
        }


class YahooNewsIE(YahooIE):
    IE_NAME = 'yahoo:news'
    _VALID_URL = r'http://news\.yahoo\.com/video/.*?-(?P<id>\d*?)\.html'

    _TEST = {
        'url': 'http://news.yahoo.com/video/china-moses-crazy-blues-104538833.html',
        'md5': '67010fdf3a08d290e060a4dd96baa07b',
        'info_dict': {
            'id': '104538833',
            'ext': 'mp4',
            'title': 'China Moses Is Crazy About the Blues',
            'description': 'md5:9900ab8cd5808175c7b3fe55b979bed0',
        },
    }

    # Overwrite YahooIE properties we don't want
    _TESTS = []

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        long_id = self._search_regex(r'contentId: \'(.+?)\',', webpage, 'long id')
        return self._get_info(long_id, video_id)


class YahooSearchIE(SearchInfoExtractor):
    IE_DESC = 'Yahoo screen search'
    _MAX_RESULTS = 1000
    IE_NAME = 'screen.yahoo:search'
    _SEARCH_KEY = 'yvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }
        for pagenum in itertools.count(0): 
            result_url = 'http://video.search.yahoo.com/search/?p=%s&fr=screen&o=js&gs=0&b=%d' % (compat_urllib_parse.quote_plus(query), pagenum * 30)
            webpage = self._download_webpage(result_url, query,
                                             note='Downloading results page '+str(pagenum+1))
            info = json.loads(webpage)
            m = info['m']
            results = info['results']

            for (i, r) in enumerate(results):
                if (pagenum * 30) +i >= n:
                    break
                mobj = re.search(r'(?P<url>screen\.yahoo\.com/.*?-\d*?\.html)"', r)
                e = self.url_result('http://' + mobj.group('url'), 'Yahoo')
                res['entries'].append(e)
            if (pagenum * 30 +i >= n) or (m['last'] >= (m['total'] -1)):
                break

        return res

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
    IE_DESC = 'Yahoo screen and movies'
    _VALID_URL = r'https?://(?:screen|movies)\.yahoo\.com/.*?-(?P<id>[0-9]+)(?:-[a-z]+)?\.html'
    _TESTS = [
        {
            'url': 'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
            'md5': '4962b075c08be8690a922ee026d05e69',
            'info_dict': {
                'id': '2d25e626-2378-391f-ada0-ddaf1417e588',
                'ext': 'mp4',
                'title': 'Julian Smith & Travis Legg Watch Julian Smith',
                'description': 'Julian and Travis watch Julian Smith',
            },
        },
        {
            'url': 'http://screen.yahoo.com/wired/codefellas-s1-ep12-cougar-lies-103000935.html',
            'md5': 'd6e6fc6e1313c608f316ddad7b82b306',
            'info_dict': {
                'id': 'd1dedf8c-d58c-38c3-8963-e899929ae0a9',
                'ext': 'mp4',
                'title': 'Codefellas - The Cougar Lies with Spanish Moss',
                'description': 'Agent Topple\'s mustache does its dirty work, and Nicole brokers a deal for peace. But why is the NSA collecting millions of Instagram brunch photos? And if your waffles have nothing to hide, what are they so worried about?',
            },
        },
        {
            'url': 'https://movies.yahoo.com/video/world-loves-spider-man-190819223.html',
            'md5': '410b7104aa9893b765bc22787a22f3d9',
            'info_dict': {
                'id': '516ed8e2-2c4f-339f-a211-7a8b49d30845',
                'ext': 'mp4',
                'title': 'The World Loves Spider-Man',
                'description': '''People all over the world are celebrating the release of \"The Amazing Spider-Man 2.\" We're taking a look at the enthusiastic response Spider-Man has received from viewers all over the world.''',
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        items_json = self._search_regex(
            r'mediaItems: ({.*?})$', webpage, 'items', flags=re.MULTILINE,
            default=None)
        if items_json is None:
            CONTENT_ID_REGEXES = [
                r'YUI\.namespace\("Media"\)\.CONTENT_ID\s*=\s*"([^"]+)"',
                r'root\.App\.Cache\.context\.videoCache\.curVideo = \{"([^"]+)"'
            ]
            long_id = self._search_regex(CONTENT_ID_REGEXES, webpage, 'content ID')
            video_id = long_id
        else:
            items = json.loads(items_json)
            info = items['mediaItems']['query']['results']['mediaObj'][0]
            # The 'meta' field is not always in the video webpage, we request it
            # from another page
            long_id = info['id']
        return self._get_info(long_id, video_id, webpage)

    def _get_info(self, long_id, video_id, webpage):
        query = ('SELECT * FROM yahoo.media.video.streams WHERE id="%s"'
                 ' AND plrs="86Gj0vCaSzV_Iuf6hNylf2" AND region="US"'
                 ' AND protocol="http"' % long_id)
        data = compat_urllib_parse.urlencode({
            'q': query,
            'env': 'prod',
            'format': 'json',
        })
        query_result = self._download_json(
            'http://video.query.yahoo.com/v1/public/yql?' + data,
            video_id, 'Downloading video info')
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
            'thumbnail': meta['thumbnail'] if meta.get('thumbnail') else self._og_search_thumbnail(webpage),
        }


class YahooNewsIE(YahooIE):
    IE_NAME = 'yahoo:news'
    _VALID_URL = r'http://news\.yahoo\.com/video/.*?-(?P<id>\d*?)\.html'

    _TESTS = [{
        'url': 'http://news.yahoo.com/video/china-moses-crazy-blues-104538833.html',
        'md5': '67010fdf3a08d290e060a4dd96baa07b',
        'info_dict': {
            'id': '104538833',
            'ext': 'mp4',
            'title': 'China Moses Is Crazy About the Blues',
            'description': 'md5:9900ab8cd5808175c7b3fe55b979bed0',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        long_id = self._search_regex(r'contentId: \'(.+?)\',', webpage, 'long id')
        return self._get_info(long_id, video_id, webpage)


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
                note='Downloading results page '+str(pagenum+1))
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

import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urlparse,
    determine_ext,
    clean_html,
)


class YahooIE(InfoExtractor):
    IE_DESC = u'Yahoo screen'
    _VALID_URL = r'http://screen\.yahoo\.com/.*?-(?P<id>\d*?)\.html'
    _TESTS = [
        {
            u'url': u'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
            u'file': u'214727115.flv',
            u'info_dict': {
                u'title': u'Julian Smith & Travis Legg Watch Julian Smith',
                u'description': u'Julian and Travis watch Julian Smith',
            },
            u'params': {
                # Requires rtmpdump
                u'skip_download': True,
            },
        },
        {
            u'url': u'http://screen.yahoo.com/wired/codefellas-s1-ep12-cougar-lies-103000935.html',
            u'file': u'103000935.flv',
            u'info_dict': {
                u'title': u'Codefellas - The Cougar Lies with Spanish Moss',
                u'description': u'Agent Topple\'s mustache does its dirty work, and Nicole brokers a deal for peace. But why is the NSA collecting millions of Instagram brunch photos? And if your waffles have nothing to hide, what are they so worried about?',
            },
            u'params': {
                # Requires rtmpdump
                u'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        items_json = self._search_regex(r'YVIDEO_INIT_ITEMS = ({.*?});$',
            webpage, u'items', flags=re.MULTILINE)
        items = json.loads(items_json)
        info = items['mediaItems']['query']['results']['mediaObj'][0]
        # The 'meta' field is not always in the video webpage, we request it
        # from another page
        long_id = info['id']
        query = ('SELECT * FROM yahoo.media.video.streams WHERE id="%s"'
                 ' AND plrs="86Gj0vCaSzV_Iuf6hNylf2"' % long_id)
        data = compat_urllib_parse.urlencode({
            'q': query,
            'env': 'prod',
            'format': 'json',
        })
        query_result_json = self._download_webpage(
            'http://video.query.yahoo.com/v1/public/yql?' + data,
            video_id, u'Downloading video info')
        query_result = json.loads(query_result_json)
        info = query_result['query']['results']['mediaObj'][0]
        meta = info['meta']

        formats = []
        for s in info['streams']:
            format_info = {
                'width': s.get('width'),
                'height': s.get('height'),
                'bitrate': s.get('bitrate'),
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
                format_info['ext'] = determine_ext(format_url)
                
            formats.append(format_info)
        formats = sorted(formats, key=lambda f:(f['height'], f['width']))

        info = {
            'id': video_id,
            'title': meta['title'],
            'formats': formats,
            'description': clean_html(meta['description']),
            'thumbnail': meta['thumbnail'],
        }
        # TODO: Remove when #980 has been merged
        info.update(formats[-1])

        return info


class YahooSearchIE(SearchInfoExtractor):
    IE_DESC = u'Yahoo screen search'
    _MAX_RESULTS = 1000
    IE_NAME = u'screen.yahoo:search'
    _SEARCH_KEY = 'yvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }
        for pagenum in itertools.count(0): 
            result_url = u'http://video.search.yahoo.com/search/?p=%s&fr=screen&o=js&gs=0&b=%d' % (compat_urllib_parse.quote_plus(query), pagenum * 30)
            webpage = self._download_webpage(result_url, query,
                                             note='Downloading results page '+str(pagenum+1))
            info = json.loads(webpage)
            m = info[u'm']
            results = info[u'results']

            for (i, r) in enumerate(results):
                if (pagenum * 30) +i >= n:
                    break
                mobj = re.search(r'(?P<url>screen\.yahoo\.com/.*?-\d*?\.html)"', r)
                e = self.url_result('http://' + mobj.group('url'), 'Yahoo')
                res['entries'].append(e)
            if (pagenum * 30 +i >= n) or (m[u'last'] >= (m[u'total'] -1)):
                break

        return res

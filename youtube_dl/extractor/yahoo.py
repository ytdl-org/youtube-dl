# coding: utf-8
from __future__ import unicode_literals

import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    clean_html,
    unescapeHTML,
    ExtractorError,
    int_or_none,
    mimetype2ext,
)

from .nbc import NBCSportsVPlayerIE


class YahooIE(InfoExtractor):
    IE_DESC = 'Yahoo screen and movies'
    _VALID_URL = r'(?P<url>(?P<host>https?://(?:[a-zA-Z]{2}\.)?[\da-zA-Z_-]+\.yahoo\.com)/(?:[^/]+/)*(?P<display_id>.+)?-(?P<id>[0-9]+)(?:-[a-z]+)?\.html)'
    _TESTS = [
        {
            'url': 'http://screen.yahoo.com/julian-smith-travis-legg-watch-214727115.html',
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
            'url': 'https://tw.screen.yahoo.com/election-2014-askmayor/敢問市長-黃秀霜批賴清德-非常高傲-033009720.html',
            'md5': '3a09cf59349cfaddae1797acc3c087fc',
            'info_dict': {
                'id': 'cac903b3-fcf4-3c14-b632-643ab541712f',
                'ext': 'mp4',
                'title': '敢問市長／黃秀霜批賴清德「非常高傲」',
                'description': '直言台南沒捷運 交通居五都之末',
                'duration': 396,
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
            'url': 'https://ca.finance.yahoo.com/news/hackers-sony-more-trouble-well-154609075.html',
            'md5': '226a895aae7e21b0129e2a2006fe9690',
            'info_dict': {
                'id': 'e624c4bc-3389-34de-9dfc-025f74943409',
                'ext': 'mp4',
                'title': '\'The Interview\' TV Spot: War',
                'description': 'The Interview',
                'duration': 30,
            }
        }, {
            'url': 'http://news.yahoo.com/video/china-moses-crazy-blues-104538833.html',
            'md5': '88e209b417f173d86186bef6e4d1f160',
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
            'url': 'https://www.yahoo.com/movies/v/true-story-trailer-173000497.html',
            'md5': '989396ae73d20c6f057746fb226aa215',
            'info_dict': {
                'id': '071c4013-ce30-3a93-a5b2-e0413cd4a9d1',
                'ext': 'mp4',
                'title': '\'True Story\' Trailer',
                'description': 'True Story',
                'duration': 150,
            },
        }, {
            'url': 'https://gma.yahoo.com/pizza-delivery-man-surprised-huge-tip-college-kids-195200785.html',
            'only_matching': True,
        }, {
            'note': 'NBC Sports embeds',
            'url': 'http://sports.yahoo.com/blogs/ncaab-the-dagger/tyler-kalinoski-s-buzzer-beater-caps-davidson-s-comeback-win-185609842.html?guid=nbc_cbk_davidsonbuzzerbeater_150313',
            'info_dict': {
                'id': '9CsDKds0kvHI',
                'ext': 'flv',
                'description': 'md5:df390f70a9ba7c95ff1daace988f0d8d',
                'title': 'Tyler Kalinoski hits buzzer-beater to lift Davidson',
            }
        }, {
            'url': 'https://tw.news.yahoo.com/-100120367.html',
            'only_matching': True,
        }, {
            # Query result is embedded in webpage, but explicit request to video API fails with geo restriction
            'url': 'https://screen.yahoo.com/community/communitary-community-episode-1-ladders-154501237.html',
            'md5': '4fbafb9c9b6f07aa8f870629f6671b35',
            'info_dict': {
                'id': '1f32853c-a271-3eef-8cb6-f6d6872cb504',
                'ext': 'mp4',
                'title': 'Communitary - Community Episode 1: Ladders',
                'description': 'md5:8fc39608213295748e1e289807838c97',
                'duration': 1646,
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id') or self._match_id(url)
        page_id = mobj.group('id')
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
        # Look for NBCSports iframes
        nbc_sports_url = NBCSportsVPlayerIE._extract_url(webpage)
        if nbc_sports_url:
            return self.url_result(nbc_sports_url, 'NBCSportsVPlayer')

        # Query result is often embedded in webpage as JSON. Sometimes explicit requests
        # to video API results in a failure with geo restriction reason therefore using
        # embedded query result when present sounds reasonable.
        config_json = self._search_regex(
            r'window\.Af\.bootstrap\[[^\]]+\]\s*=\s*({.*?"applet_type"\s*:\s*"td-applet-videoplayer".*?});(?:</script>|$)',
            webpage, 'videoplayer applet', default=None)
        if config_json:
            config = self._parse_json(config_json, display_id, fatal=False)
            if config:
                sapi = config.get('models', {}).get('applet_model', {}).get('data', {}).get('sapi')
                if sapi:
                    return self._extract_info(display_id, sapi, webpage)

        items_json = self._search_regex(
            r'mediaItems: ({.*?})$', webpage, 'items', flags=re.MULTILINE,
            default=None)
        if items_json is None:
            CONTENT_ID_REGEXES = [
                r'YUI\.namespace\("Media"\)\.CONTENT_ID\s*=\s*"([^"]+)"',
                r'root\.App\.Cache\.context\.videoCache\.curVideo = \{"([^"]+)"',
                r'"first_videoid"\s*:\s*"([^"]+)"',
                r'%s[^}]*"ccm_id"\s*:\s*"([^"]+)"' % re.escape(page_id),
            ]
            video_id = self._search_regex(CONTENT_ID_REGEXES, webpage, 'content ID')
        else:
            items = json.loads(items_json)
            info = items['mediaItems']['query']['results']['mediaObj'][0]
            # The 'meta' field is not always in the video webpage, we request it
            # from another page
            video_id = info['id']
        return self._get_info(video_id, display_id, webpage)

    def _extract_info(self, display_id, query, webpage):
        info = query['query']['results']['mediaObj'][0]
        meta = info.get('meta')
        video_id = info.get('id')

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
                if s.get('format') == 'm3u8_playlist':
                    format_info['protocol'] = 'm3u8_native'
                    format_info['ext'] = 'mp4'
                format_url = compat_urlparse.urljoin(host, path)
                format_info['url'] = format_url
            formats.append(format_info)

        self._sort_formats(formats)

        closed_captions = self._html_search_regex(
            r'"closedcaptions":(\[[^\]]+\])', webpage, 'closed captions',
            default='[]')

        cc_json = self._parse_json(closed_captions, video_id, fatal=False)
        subtitles = {}
        if cc_json:
            for closed_caption in cc_json:
                lang = closed_caption['lang']
                if lang not in subtitles:
                    subtitles[lang] = []
                subtitles[lang].append({
                    'url': closed_caption['url'],
                    'ext': mimetype2ext(closed_caption['content_type']),
                })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': unescapeHTML(meta['title']),
            'formats': formats,
            'description': clean_html(meta['description']),
            'thumbnail': meta['thumbnail'] if meta.get('thumbnail') else self._og_search_thumbnail(webpage),
            'duration': int_or_none(meta.get('duration')),
            'subtitles': subtitles,
        }

    def _get_info(self, video_id, display_id, webpage):
        region = self._search_regex(
            r'\\?"region\\?"\s*:\s*\\?"([^"]+?)\\?"',
            webpage, 'region', fatal=False, default='US')
        data = compat_urllib_parse.urlencode({
            'protocol': 'http',
            'region': region,
        })
        query_url = (
            'https://video.media.yql.yahoo.com/v1/video/sapi/streams/'
            '{id}?{data}'.format(id=video_id, data=data))
        query_result = self._download_json(
            query_url, display_id, 'Downloading video info')
        return self._extract_info(display_id, query_result, webpage)


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

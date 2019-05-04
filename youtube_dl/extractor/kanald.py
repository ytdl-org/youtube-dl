# coding: utf-8
from __future__ import unicode_literals

from re import findall

from .common import InfoExtractor
from ..compat import compat_str


class KanaldIE(InfoExtractor):
    "Kanal D TV Website extractor"
    IE_NAME = 'Kanal D'
    _VALID_URL = r'https?://(?:www\.)?kanald\.com\.tr/(?:.*)/(?P<id>.*\d+.*bolum(?!ler).*)/?'
    _TESTS = [{
        'url': 'https://www.kanald.com.tr/kuzeyguney/1-bolum/10115',
        'md5': '88d518f7803b53e9e6187b05fe0f1a63',
        'info_dict': {
            'id': '1-bolum/10115',
            'ext': 'm3u8',
            'title': '1.Bölüm',
            'release_date': '20110907',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Kanal D',
            'description': '1.Bölüm'
        }
    }, {
        'url':
        'https://www.kanald.com.tr/sevdanin-bahcesi/bolumler/sevdanin-bahcesi-2-bolum',
        'only_matching': True
    }, {
        'url':
        'https://www.kanald.com.tr/yarim-elma/bolum/yarim-elma-36-bolum',
        'only_matching': True
    }, {
        'url':
        'https://www.kanald.com.tr/ask-ve-gunah/bolumler/ask-ve-gunah-120-bolum-final',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        video_url = "https://soledge13.dogannet.tv/" + self._search_regex(
            r'["\']contentUrl["\']:["\'](?P<video_url>.*)["\']', webpage,
            'video_url')
        formats = self._extract_m3u8_formats(video_url, video_id)
        thumbnail = self._search_regex(
            r'<meta itemprop=["\']thumbnailUrl["\'] content=["\'](?P<thumbnail>.*)["\'].*',
            webpage, 'thumbnail')
        description = self._og_search_description(webpage)
        year = self._search_regex(
            r'["\']uploadDate["\']:["\'](?P<year>\d{4}).*["\']', webpage,
            'year')
        month = self._search_regex(
            r'["\']uploadDate["\']:["\']\d{4}-(?P<month>\d\d).*["\']', webpage,
            'month')
        day = self._search_regex(
            r'["\']uploadDate["\']:["\']\d{4}-\d\d-(?P<day>\d\d).*["\']',
            webpage, 'day')
        release_date = year + month + day

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'url': video_url,
            'uploader': compat_str('Kanal D'),
            'release_date': release_date
        }


class KanaldSerieIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kanald\.com\.tr/(?P<id>.*)/(?:bolum|bolumler)$'
    IE_NAME = 'Kanal D:serie'
    _TESTS = [{
        'url': 'https://www.kanald.com.tr/kuzeyguney/bolum',
        'info_dict': {
            'id': 'kuzeyguney'
        },
        'playlist_mincount': 80
    }, {
        'url': 'https://www.kanald.com.tr/iki-yalanci/bolumler',
        'only_matching': True
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        next_page = url
        webpage = None
        page = 1
        has_more = True
        entries = []

        while has_more:
            webpage = self._download_webpage(next_page,
                                             playlist_id,
                                             note='Downloading page %s' % page)

            try:
                next_page = 'https://www.kanald.com.tr' + self._search_regex(
                    r'class=["\']next["\']><a href=["\'](?P<hasmore>.*)["\']>.*</a>',
                    webpage,
                    'hasmore',
                    default=None,
                    fatal=False)
                page += 1
            except TypeError:
                has_more = False

            page_entries = findall(
                r'<a.*class=["\']title["\'].*href=["\'](?P<relative>.*)["\'].*',
                webpage)

            for entry in page_entries:
                entries.append(
                    self.url_result('https://www.kanald.com.tr%s' % entry,
                                    ie=KanaldIE.ie_key()))

        return self.playlist_result(entries, playlist_id)

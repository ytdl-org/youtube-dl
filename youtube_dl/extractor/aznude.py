# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import re


class AZNudeIE(InfoExtractor):
    IE_NAME = "aznude"
    _VALID_URL = r'https?://(?:www\.)?aznude\.com/(?:mrskin|azncdn)/[^/?]+/[^/?]+/(?P<id>.*)\.html'
    _TEST = {
        'url': 'https://www.aznude.com/mrskin/marisatomei/loiteringwithintent/loiteringwithintent-mcnallytomei-hd-01-hd.html',
        'md5': '28973bf7b818edfe55677b67bc073e40',
        'info_dict': {
            'id': 'loiteringwithintent-mcnallytomei-hd-01-hd',
            'ext': 'mp4',
            'title': 'Marisa Tomei in Loitering With Intent - 01',
            'thumbnail': 'https://cdn1.aznude.com/marisatomei/loiteringwithintent/LoiteringWithIntent-McNallyTomei-HD-01-gigantic-4.jpg',
            'description': 'Watch Marisa Tomei\'s Breasts scene on AZNude for free (22 seconds).',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        numeric_id = "-".join(re.findall(r'(?P<num>(?:s\d+e\d+)|(?:\d+[xX]\d+)|(?:\d+))', video_id))
        webpage = self._download_webpage(url, video_id)

        artist = self._search_regex(r'<span><a href="/view/celeb/[^/?]/[^/?]+\.html">(?P<artist>[^<]+)</a></span>',
                                    webpage,
                                    url,
                                    default=None)
        work = self._search_regex(r'in <a href="/view/movie/[^/?]/[^/?]+\.html">(?P<work>[^<]+)</a>',
                                  webpage,
                                  url,
                                  default=None)

        if (artist is not None) and (work is not None):
            title = artist + " in " + work
        else:
            title = self._og_search_title(webpage)

        return {
            'id': video_id,
            'title': title + " - " + numeric_id,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'url': self._search_regex(r'(?:<a href=")(?P<url>(https?:)?//[^/]*\.aznude\.com/.*\.mp4)(?:"><div class="videoButtons"><i class="fa"></i>Download</div></a>)',
                                      webpage,
                                      'url',
                                      fatal=True)
        }


class AZNudeMultiPageBaseIE(InfoExtractor):
    def _extract_entries(self, webpage, regex, prefix):
        for url in re.findall(regex, webpage):
            yield self.url_result(prefix + url, AZNudeIE.ie_key())

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        parse_result = urlparse(url)
        url_prefix = parse_result.scheme + "://" + parse_result.netloc

        entries = self._extract_entries(webpage, self._get_entry_regex(page_id), url_prefix)
        return self.playlist_result(entries, page_id, self._get_webpage_title(webpage))

    def _get_webpage_title(self, webpage):
        return self._search_regex(r'(?:<title>)(?P<title>.+)(?:</title>)', webpage, 'title', default=None, fatal=False).title()

    def _get_entry_regex(self, page_id):
        return ""


class AZNudeCelebIE(AZNudeMultiPageBaseIE):
    IE_NAME = "aznude:celeb"
    _VALID_URL = r'https?://(?:www\.)?aznude\.com/view/celeb/[^/?]/(?P<id>.+)\.html'
    _TEST = {
        'url': 'http://www.aznude.com/view/celeb/m/marisatomei.html',
        'info_dict': {
            'title': 'Marisa Tomei',
            'id': 'marisatomei',
        },
        'playlist_mincount': 33,
    }

    def _get_webpage_title(self, webpage):
        return self._search_regex(r'(?:<title>)(?P<title>.+)(?: Nude - AZNude </title>)', webpage, 'title', default=None).title()

    def _get_entry_regex(self, page_id):
        return r'(?:href=")(?P<url>/(?:mrskin|azncdn)/' + page_id + '/[^"]*)'


class AZNudeMovieIE(AZNudeMultiPageBaseIE):
    IE_NAME = "aznude:movie"
    _VALID_URL = r'https?://(?:www\.)?aznude\.com/view/movie/[^/?]/(?P<id>.+)\.html'
    _TEST = {
        'url': 'https://www.aznude.com/view/movie/l/loiteringwithintent.html',
        'info_dict': {
            'title': 'Loitering With Intent',
            'id': 'loiteringwithintent',
        },
        'playlist_mincount': 2,
    }

    def _get_webpage_title(self, webpage):
        return self._search_regex(r'(?:<title>)(?P<title>.+)(?: NUDE SCENES - AZNude</title>)', webpage, 'title', default=None).title()

    def _get_entry_regex(self, page_id):
        return r'(?:href=")(?P<url>/(?:mrskin|azncdn)/[^/?]+/' + page_id + '/[^"]*)'

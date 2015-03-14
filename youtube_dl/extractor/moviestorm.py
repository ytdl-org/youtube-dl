# coding: utf-8
from __future__ import unicode_literals

import os.path
import re
from time import sleep

from .common import InfoExtractor
from ..utils import ExtractorError
from ..compat import (
    compat_html_parser,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
)

class MovieStormHTMLParser(compat_html_parser.HTMLParser):
    def __init__(self):
        self.found_button = False
        self.watch_urls = []
        self.direct_url = False
        compat_html_parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        attrs = dict((k, v) for k, v in attrs)
        if tag == 'td' and attrs['class'] == 'link_td':
            self.found_button = True
        elif tag == 'a' and self.found_button:
            # suppress ishare and other direct links, can't handle now
            if 'moviestorm' in attrs['href']:
                self.watch_urls.append(attrs['href'].strip())
        elif tag == 'a' and 'class' in attrs and attrs['class'] == 'real_link':
            self.direct_url = attrs['href'].strip()

    def handle_endtag(self, tag):
        if tag == 'td':
            self.found_button = False

    @classmethod
    def extract_watch_urls(cls, html):
        p = cls()
        p.feed(html)
        p.close()
        return p.watch_urls

    @classmethod
    def extract_direct_url(cls, html):
        p = cls()
        p.feed(html)
        p.close()
        return p.direct_url

class MovieStormIE(InfoExtractor):
    IE_DESC = 'Movie Storm (link farm)'
    IE_NAME = 'MovieStorm'
    _VALID_URL = r'http://moviestorm\.eu/view/(\d+)-watch-(.*)/season-(\d+)/episode-(\d+)'
    _LINK_FARM = True

    # There are no tests for this IE because the links on any given moviestorm
    # page can dynamically change, and because the actual download/extraction
    # is ultimately preformed by another IE. An example of an acceptable url to
    # feed to this IE is: http://moviestorm.eu/view/218-watch-the-simpsons/season-26/episode-1
    _TEST = False

    # moviestorm's drupal db config is unstable at times
    # retry up to 5 times before giving up, 5 second delay
    # between each retry
    retry_count = 0
    max_retries = 5
    retry_wait = 5
    direct_urls = []

    def _parse_target(self, target):
        uri = compat_urlparse.urlparse(target)
        hash = uri.fragment[1:].split('?')[0]
        token = os.path.basename(hash.rstrip('/'))
        return (uri, hash, token)

    def _real_extract(self, url):
        # retry loop to capture moviestorm page
        while True:
            if self.retry_count == 0:
                note = 'Downloading link farm page'
            else:
                note = ('Unstable db connection, retying again in %s seconds '
                    '[%s/%s]' % (self.retry_wait, self.retry_count,
                    self.max_retries))

            (_, _, token) = self._parse_target(url)
            farmpage = self._download_webpage(
                url, token,
                note=note,
                errnote='Unable to download link farm page',
                fatal=False
            )

            if farmpage.strip() != 'MySQL server has gone away':
                break

            if self.retry_count < self.max_retries:
                self.retry_count += 1
                sleep(self.retry_wait)
            else:
                msg = 'The moviestorm database is currently unstable.  Please try again later.'
                raise ExtractorError(msg, expected=True)

        # scrape WATCH button links from moviestorm page
        self.to_screen(': Extracting watch page urls')
        watch_urls = MovieStormHTMLParser.extract_watch_urls(farmpage)

        # get direct urls from scraped watch pages
        self.to_screen(': Extracting direct links from watch pages')
        for watch_url in watch_urls:
            (_, _, token) = self._parse_target(watch_url)
            watchpage = self._download_webpage(
                watch_url, token,
                note=False,
                errnote='Unable to download link farm watch page',
                fatal=False
        	)

        	if watchpage is not None:
        	    direct_url = MovieStormHTMLParser.extract_direct_url(watchpage)
        	    if direct_url:
        	        self.direct_urls.append(direct_url)

        self.to_screen(': Passing off farmed links to InfoExtractors')
        return list(set(self.direct_urls))

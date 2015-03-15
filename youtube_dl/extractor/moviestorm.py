# coding: utf-8
from __future__ import unicode_literals

import os.path
from time import sleep

from .common import InfoExtractor
from ..utils import ExtractorError
from ..compat import (
    compat_html_parser,
    compat_urlparse
)


class MovieStormHTMLParser(compat_html_parser.HTMLParser):
    def __init__(self):
        self.found_button = False
        self.watch_urls = []
        self.direct_url = False
        self.series_home_page = False
        compat_html_parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        attrs = dict((k, v) for k, v in attrs)
        if tag == 'td' and attrs['class'] == 'link_td':
            self.found_button = True
        elif tag == 'a' and self.found_button:
            # Suppress ishare and other direct links, can't handle now
            if 'moviestorm' in attrs['href']:
                self.watch_urls.append(attrs['href'].strip())
        elif tag == 'a' and 'class' in attrs and attrs['class'] == 'real_link':
            self.direct_url = attrs['href'].strip()

    def handle_endtag(self, tag):
        if tag == 'td':
            self.found_button = False

    def handle_data(self, data):
        if data.strip() == 'SHOW EPISODES':
            self.series_home_page = True

    @classmethod
    def custom_parse(cls, html, return_variable):
        p = cls()
        p.feed(html)
        p.close()
        return getattr(p, return_variable)


class MovieStormIE(InfoExtractor):
    """EXTRACTOR INFO:
    There are no tests for this IE because the links on any given moviestorm
    page can dynamically change, and because the actual download/extraction
    is ultimately preformed by another IE. Example urls to
    feed to this IE are:

        EPISODE: http://moviestorm.eu/view/5821-watch-portlandia/season-1/episode-1
        MOVIE:   http://moviestorm.eu/view/5269-watch-taken-3-online.html

    If the user provides a series url, like the one below, this IE should detect
    and raise an error:

        SERIES:  http://moviestorm.eu/view/5821-watch-portlandia.html

    In other news, moviestorm's drupal db config is unstable at times retry up to 5
    times before giving up, waiting 5 second delay between each retry.

    Also, this IE will catch all links with http://moviestorm.eu urls. If it's an
    un-handleable url, an error will be thrown informing the user of appropriate
    urls to provide. Not using a more complex regex is meant to prevent unacceptable
    moviestorm urls from falling back into the generic IE, as that will always fail on
    moviestorm links.
    """

    IE_DESC = 'Movie Storm (link farm)'
    IE_NAME = 'MovieStorm'
    _VALID_URL = r'http://moviestorm\.eu'
    _LINK_FARM = True
    _TEST = False

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
        # Inform user to provide proper moviestorm link
        if 'watch' not in url:
            msg = ('The moviestorm handler requires either a movie page link or '
                   'a series episode page link.  Please try again with one of those.')
            raise ExtractorError(msg, expected=True)

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
                series_home_page = MovieStormHTMLParser.custom_parse(
                    farmpage,
                    'series_home_page'
                )

                # Fail if provided series home page
                if series_home_page:
                    msg = ('It looks like you provided an show page url.  You must provide '
                           'an episode page url or movie page url')
                    raise ExtractorError(msg, expected=True)

                # Success
                break

            # Continue retrying if moviestorm database is currently unstable
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                sleep(self.retry_wait)
            else:
                msg = 'The moviestorm database is currently unstable.  Please try again later.'
                raise ExtractorError(msg, expected=True)

        # Scrape WATCH button links from moviestorm page
        self.to_screen(': Extracting watch page urls')
        watch_urls = MovieStormHTMLParser.custom_parse(
            farmpage,
            'watch_urls'
        )

        # Get direct urls from scraped watch pages
        self.to_screen(': Extracting direct links from watch pages')
        direct_url_count = 1

        for watch_url in watch_urls:
            # Stop after gathering 50 urls, moviestorm sends 503 if
            # request too many in rapid succession
            if direct_url_count < 50:
                (_, _, token) = self._parse_target(watch_url)
                watchpage = self._download_webpage(
                    watch_url, token,
                    note=False,
                    errnote='Unable to download link farm watch page',
                    fatal=False
                )

                if watchpage is not None:
                    direct_url = MovieStormHTMLParser.custom_parse(
                        watchpage,
                        'direct_url'
                    )

                    if direct_url:
                        self.direct_urls.append(direct_url)

            direct_url_count += 1

        self.to_screen(': Passing off farmed links to InfoExtractors')
        return list(set(self.direct_urls))

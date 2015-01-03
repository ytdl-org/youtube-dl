from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import clean_html, ExtractorError

try:
    import microdata
except ImportError:
    microdata = None


class WatchTvSeriesSeasonIE(InfoExtractor):
    domain_base = 'http://watch-tv-series.to/'
    _VALID_URL = domain_base + r'(?P<path>season-(?P<season>\d+)/[a-z]+)'

    def extract_microdata(self):
        item, = microdata.get_items(self.content)
        name = item.name
        playlist_title = '%s - Season %s' % (name, self.season)
        playlist_description = item.description

        season = item.season
        episodes = sorted(
            season.get_all('episode'), key=lambda ep: ep.datepublished)

        entries = [
            self.url_result(self.domain_base + ep.url.lstrip('/'),
                            'WatchTvSeriesEpisode')
            for ep in episodes
        ]

        return self.playlist_result(
            entries, playlist_id=item.url, playlist_title=playlist_title,
            playlist_description=playlist_description)

    def extract_strings(self):
        name = self._search_regex(
            r'<span itemprop="name">([^<]+)</span>',
            self.content, 'show name')

        playlist_title = '%s - Season %s' % (name, self.season)

        data = {}
        entries = []

        # This parsing is sensitive to the order of HTML attributes in the
        # content of the page, but it works for now.
        itemprop_regex = r'itemprop="([a-z]+)"(?: content="([^"]+)"|>([^<]+))'

        for mobj in re.finditer(itemprop_regex, self.content):
            key = mobj.group(1)
            value = mobj.group(2) or mobj.group(3)
            value = clean_html(value).strip()
            data[key] = value
            if key == 'name' and data.get('url', '').startswith('/episode'):
                url = self.domain_base + data['url'].lstrip('/')
                entries.append(self.url_result(url, 'WatchTvSeriesEpisode'))

        # Episodes are displayed with the latest first,
        # but we want to retrieve the earliest first.
        entries.reverse()

        return self.playlist_result(
            entries, playlist_id=self.path, playlist_title=playlist_title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        self.path = mobj.group('path')
        self.season = mobj.group('season')
        self.content = self._download_webpage(url, self.path)
        if microdata:
            return self.extract_microdata()
        else:
            return self.extract_strings()


class WatchTvSeriesEpisodeIE(InfoExtractor):
    domain_base = 'http://watch-tv-series.to/'
    _VALID_URL = 'http://watch-tv-series.to/(?P<path>episode/[a-z_0-9]+.html)'

    def _real_extract(self, url):
        # There is microdata on this page, but we don't need it,
        # since we will return a url_result anyway.

        mobj = re.match(self._VALID_URL, url)
        path = mobj.group('path')

        content = self._download_webpage(url, path)

        movshare_regex = (
            r'href="/([^"]+)" class="buttonlink" title="movshare.net"')

        mobj = re.search(movshare_regex, content)
        if mobj is None:
            raise ExtractorError(
                'Unable to extract movshare.net link. ' +
                'No other video sites are supported.',
                expected=True)

        external_link = self._download_webpage(
            self.domain_base + mobj.group(1), path + '[external]')

        mobj = re.search(
            r'http://www.movshare.net/video/[a-z0-9]+', external_link)

        return self.url_result(mobj.group(0))

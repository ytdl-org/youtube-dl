# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class PonyFMIE(InfoExtractor):
    """
    InfoExtractor for PonyFM

    This extractor is for tracks. Playlists and Albums may be defined at a later
    point using a separate class that will be in this file.
    """
    _VALID_URL = r'https?://pony\.fm/tracks/(?P<id>\d+)-.+'
    _TESTS = []

    def _real_extract(self, url):
        track_id = self._match_id(url)

        # Extract required fields from webpage
        webpage = self._download_webpage(url, track_id)
        title = self._html_search_meta(
            ['og:title', 'twitter:title'], webpage) or self._html_search_regex(
            r'<h1>([^<]+</h1>', webpage, "title"
        )

        # Create formats array from track_id
        formats = []
        base_url = "https://pony.fm/t%s" % track_id
        formats.extend([
            {'url': "%s/dl.mp3" % base_url},
            {'url': "%s/dl.m4a" % base_url},
            {'url': "%s/dl.ogg" % base_url},
            {'url': "%s/dl.flac" % base_url}
        ])

        extracted = {
            'id': track_id,
            'title': title,
            'formats': formats,
        }

        # Extract optional metadata (author, album art) from webpage
        artwork = self._html_search_meta(['og:image'], webpage)
        author = self._search_regex(
            r'by: <a [^>]+>([^<]+)</a>', webpage, "author", fatal=False
        )

        if artwork:
            extracted['thumbnail'] = artwork
        if author:
            extracted['uploader'] = author

        return extracted

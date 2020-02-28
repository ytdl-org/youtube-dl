# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MatterIE(InfoExtractor):
    """
    InfoExtractor for Matter Music

    This class should be used to handle tracks. Another class (TODO) will be
    used to implement playlists or other content.
    """
    _VALID_URL = r'https?://app.matter.online/tracks/(?P<id>\d+)/?'
    _TESTS = {
        # TODO: Implement
    }

    def _real_extract(self, url):
        track_id = self._match_id(url)
        webpage = self._download_webpage(
            "https://api.matter.online/api/v1/open-graph/tracks/%s/embedded" % track_id, track_id
        )

        author = self._html_search_regex(
            r'<a href="https://app.matter.online/artists/[^"]+" target="[^"]+">([^<]+)</a>',
            webpage, "author"
        )
        title = self._html_search_regex(
            r'<a href="https://app.matter.online/tracks/\d+" target="[^"]+">([^<]+)</a>',
            webpage, "title"
        )
        download_url = self._html_search_regex(
            r'<source src="(https://matter-production.s3.amazonaws.com/audios/[^\.]+\.[^"]+)"/>',
            webpage, "download_url"
        )
        artwork = self._html_search_regex(
            r'style="background: url\((https://matter-production.s3.amazonaws.com/images/[^\.]+\.[^\)]+)\)',
            webpage, "artwork"
        )

        return {
            'id': track_id,
            'url': download_url,
            'title': title,
            'uploader': author,
            'thumbnail': artwork,
        }

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
    _TESTS = [{
        'url': 'https://app.matter.online/tracks/12866',
        'info_dict': {
            'id': '12866',
            'ext': 'mp3',
            'title': 'Beautiful type beat',
            'uploader': 'internet user',
        },
    }, {
        'url': 'https://app.matter.online/tracks/18891',
        'info_dict': {
            'id': '18891',
            'ext': 'mp3',
            'title': 'starstruck',
            'uploader': 'iwi.',
        }
    }]

    def _real_extract(self, url):
        track_id = self._match_id(url)

        # Fetch page with metadata and download URLs.
        api = "https://api.matter.online/api/v1/open-graph/tracks/%s/embedded"
        webpage = self._download_webpage(api % track_id, track_id)

        # Extract required fields
        title = self._search_regex(
            r'tracks/\d+" target="[^"]+">([^<]+)</a>',
            webpage, "title"
        )
        download_url = self._search_regex(
            r'(https://[^/]+/audios/[^\.]+\.[^"]+)"/>',
            webpage, "download_url"
        )

        extracted = {
            'id': track_id,
            'url': download_url,
            'title': title,
        }

        # Extract optional fields
        author = self._search_regex(
            r'artists/[^"]+" target="[^"]+">([^<]+)</a>',
            webpage, "author", fatal=False
        )
        artwork = self._search_regex(
            r'(https://[^/]+/images/[^\.]+\.[^\)]+)\)',
            webpage, "artwork", fatal=False
        )

        if artwork:
            extracted['thumbnail'] = artwork
        if author:
            extracted['uploader'] = author

        return extracted

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

        # Extract required fields from JSON API
        apiurl = "https://pony.fm/api/web/tracks/%s" % track_id
        json = self._download_json(apiurl, track_id)['track']

        title = json['title']
        formats = []
        for f in json['formats']:
            formats.append({
                'format': f['name'],
                'url': f['url'],
            })

        extracted = {
            'id': track_id,
            'title': title,
            'formats': formats,
        }

        # Extract optional metadata (author, album art) from JSON API
        author = json.get('user', {}).get('name')
        artwork = json.get('covers', {}).get('original')

        if artwork:
            extracted['thumbnail'] = artwork
        if author:
            extracted['uploader'] = author

        return extracted

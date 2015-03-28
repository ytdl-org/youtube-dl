from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    parse_duration,
)


class DHMIE(InfoExtractor):
    IE_DESC = 'Filmarchiv - Deutsches Historisches Museum'
    _VALID_URL = r'http://www\.dhm\.de/filmarchiv/die-filme/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.dhm.de/filmarchiv/die-filme/the-marshallplan-at-work-in-west-germany/',
        'md5': '11c475f670209bf6acca0b2b7ef51827',
        'info_dict': {
            'id': 'the-marshallplan-at-work-in-west-germany',
            'ext': 'flv',
            'title': 'MARSHALL PLAN AT WORK IN WESTERN GERMANY, THE',
            'description': 'md5:1fabd480c153f97b07add61c44407c82',
            'duration': 660,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        playlist_url = self._search_regex(
            r"file\s*:\s*'([^']+)'", webpage, 'playlist url')

        playlist = self._download_xml(playlist_url, video_id)

        track = playlist.find(
            './{http://xspf.org/ns/0/}trackList/{http://xspf.org/ns/0/}track')

        video_url = xpath_text(
            track, './{http://xspf.org/ns/0/}location',
            'video url', fatal=True)
        thumbnail = xpath_text(
            track, './{http://xspf.org/ns/0/}image',
            'thumbnail')

        title = self._search_regex(
            [r'dc:title="([^"]+)"', r'<title> &raquo;([^<]+)</title>'],
            webpage, 'title').strip()
        description = self._html_search_regex(
            r'<p><strong>Description:</strong>(.+?)</p>',
            webpage, 'description', fatal=False)
        duration = parse_duration(self._search_regex(
            r'<em>Length\s*</em>\s*:\s*</strong>([^<]+)',
            webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
        }

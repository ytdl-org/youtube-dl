from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    xpath_text,
    xpath_with_ns,
)


class BdsmstreakIE(InfoExtractor):
    IE_NAME = 'bdsmstreak'
    _VALID_URL = r'https?://(?:www\.)?bdsmstreak\.com/video/(?P<id>[0-9]+)/'
    _API_URL = 'http://www.bdsmstreak.com/media/nuevo/playlist.php?key={0:}'
    _TEST = {
        'url': 'http://www.bdsmstreak.com/video/21668/ride-the-horse',
        'md5': 'a0b91a1579ce92af6b064f312646c00b',
        'info_dict': {
            'id': '21668',
            'ext': 'mp4',
            'title': 'Ride the horse',
            'thumbnail': 'http://www.bdsmstreak.com/media/videos/tmb/21668/20.jpg',
            'duration': 1302.15,
            'age_limit': 18,
        }
    }

    # This is similar to `InfoExtractor._parse_xspf()`, but the tag names are different
    # This method is being called from `InfoExtractor._extract_xspf_playlist()`
    def _parse_xspf(self, playlist, playlist_id):
        NS_MAP = {
            'xspf': 'http://xspf.org/ns/0/',
        }

        entries = []
        for track in playlist.findall(xpath_with_ns('./xspf:trackList/xspf:track', NS_MAP)):
            title = xpath_text(
                track, xpath_with_ns('./xspf:title', NS_MAP), default=playlist_id)
            thumbnail = xpath_text(
                track, xpath_with_ns('./xspf:thumb', NS_MAP))
            duration = float_or_none(
                xpath_text(track, xpath_with_ns('./xspf:duration', NS_MAP)))
            # TODO: 2 formats, flv and mp4
            formats = [{
                'url': xpath_text(
                    track, xpath_with_ns('./xspf:html5', NS_MAP)
                )
            }]
            self._sort_formats(formats)

            entries.append({
                'id': playlist_id,
                'title': title,
                # 'description': description, # The description is in the webpage itself, but we don't even download that
                'thumbnail': thumbnail,
                'duration': duration,
                'formats': formats,
                'age_limit': 18,
            })
        return entries

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        playlist_url = self._API_URL.format(playlist_id)
        entries = self._extract_xspf_playlist(playlist_url, playlist_id)
        return self.playlist_result(entries, playlist_id)

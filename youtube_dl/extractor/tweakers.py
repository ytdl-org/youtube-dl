from __future__ import unicode_literals

from .common import InfoExtractor


class TweakersIE(InfoExtractor):
    _VALID_URL = r'https?://tweakers\.net/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://tweakers.net/video/9926/new-nintendo-3ds-xl-op-alle-fronten-beter.html',
        'md5': '3147e4ddad366f97476a93863e4557c8',
        'info_dict': {
            'id': '9926',
            'ext': 'mp4',
            'title': 'New Nintendo 3DS XL - Op alle fronten beter',
            'description': 'md5:f97324cc71e86e11c853f0763820e3ba',
            'thumbnail': 're:^https?://.*\.jpe?g$',
            'duration': 386,
        }
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        entries = self._extract_xspf_playlist(
            'https://tweakers.net/video/s1playlist/%s/playlist.xspf' % playlist_id, playlist_id)
        return self.playlist_result(entries, playlist_id)

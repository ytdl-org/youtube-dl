from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    xpath_with_ns,
    int_or_none,
    float_or_none,
)


class TweakersIE(InfoExtractor):
    _VALID_URL = r'https?://tweakers\.net/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://tweakers.net/video/9926/new-nintendo-3ds-xl-op-alle-fronten-beter.html',
        'md5': '1b5afa817403bb5baa08359dca31e6df',
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
        video_id = self._match_id(url)

        playlist = self._download_xml(
            'https://tweakers.net/video/s1playlist/%s/playlist.xspf' % video_id,
            video_id)

        NS_MAP = {
            'xspf': 'http://xspf.org/ns/0/',
            's1': 'http://static.streamone.nl/player/ns/0',
        }

        track = playlist.find(xpath_with_ns('./xspf:trackList/xspf:track', NS_MAP))

        title = xpath_text(
            track, xpath_with_ns('./xspf:title', NS_MAP), 'title')
        description = xpath_text(
            track, xpath_with_ns('./xspf:annotation', NS_MAP), 'description')
        thumbnail = xpath_text(
            track, xpath_with_ns('./xspf:image', NS_MAP), 'thumbnail')
        duration = float_or_none(
            xpath_text(track, xpath_with_ns('./xspf:duration', NS_MAP), 'duration'),
            1000)

        formats = [{
            'url': location.text,
            'format_id': location.get(xpath_with_ns('s1:label', NS_MAP)),
            'width': int_or_none(location.get(xpath_with_ns('s1:width', NS_MAP))),
            'height': int_or_none(location.get(xpath_with_ns('s1:height', NS_MAP))),
        } for location in track.findall(xpath_with_ns('./xspf:location', NS_MAP))]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }

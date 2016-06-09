from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE
from ..utils import js_to_json


class GodTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?god\.tv(?:/[^/]+)*/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://god.tv/jesus-image/video/jesus-conference-2016/randy-needham',
        'info_dict': {
            'id': 'lpd3g2MzE6D1g8zFAKz8AGpxWcpu6o_3',
            'ext': 'mp4',
            'title': 'Randy Needham',
            'duration': 3615.08,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'http://god.tv/playlist/bible-study',
        'info_dict': {
            'id': 'bible-study',
        },
        'playlist_mincount': 37,
    }, {
        'url': 'http://god.tv/node/15097',
        'only_matching': True,
    }, {
        'url': 'http://god.tv/live/africa',
        'only_matching': True,
    }, {
        'url': 'http://god.tv/liveevents',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        settings = self._parse_json(
            self._search_regex(
                r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'settings', default='{}'),
            display_id, transform_source=js_to_json, fatal=False)

        ooyala_id = None

        if settings:
            playlist = settings.get('playlist')
            if playlist and isinstance(playlist, list):
                entries = [
                    OoyalaIE._build_url_result(video['content_id'])
                    for video in playlist if video.get('content_id')]
                if entries:
                    return self.playlist_result(entries, display_id)
            ooyala_id = settings.get('ooyala', {}).get('content_id')

        if not ooyala_id:
            ooyala_id = self._search_regex(
                r'["\']content_id["\']\s*:\s*(["\'])(?P<id>[\w-]+)\1',
                webpage, 'ooyala id', group='id')

        return OoyalaIE._build_url_result(ooyala_id)

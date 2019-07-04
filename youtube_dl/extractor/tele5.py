# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .nexx import NexxIE
from ..compat import compat_urlparse


class Tele5IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tele5\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.tele5.de/mediathek/filme-online/videos?vid=1549416',
        'info_dict': {
            'id': '1549416',
            'ext': 'mp4',
            'upload_date': '20180814',
            'timestamp': 1534290623,
            'title': 'Pandorum',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.tele5.de/kalkofes-mattscheibe/video-clips/politik-und-gesellschaft?ve_id=1551191',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/video-clip/?ve_id=1609440',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/filme/schlefaz-dragon-crusaders/',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/filme/making-of/avengers-endgame/',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/star-trek/raumschiff-voyager/ganze-folge/das-vinculum/',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/anders-ist-sevda/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        video_id = (qs.get('vid') or qs.get('ve_id') or [None])[0]

        if not video_id:
            display_id = self._match_id(url)
            webpage = self._download_webpage(url, display_id)
            video_id = self._html_search_regex(
                (r'id\s*=\s*["\']video-player["\'][^>]+data-id\s*=\s*["\'](\d+)',
                 r'\s+id\s*=\s*["\']player_(\d{6,})',
                 r'\bdata-id\s*=\s*["\'](\d{6,})'), webpage, 'video id')

        return self.url_result(
            'https://api.nexx.cloud/v3/759/videos/byid/%s' % video_id,
            ie=NexxIE.ie_key(), video_id=video_id)

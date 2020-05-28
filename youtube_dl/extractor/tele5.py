# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .jwplatform import JWPlatformIE
from .nexx import NexxIE
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    NO_DEFAULT,
    try_get,
)


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

        NEXX_ID_RE = r'\d{6,}'
        JWPLATFORM_ID_RE = r'[a-zA-Z0-9]{8}'

        def nexx_result(nexx_id):
            return self.url_result(
                'https://api.nexx.cloud/v3/759/videos/byid/%s' % nexx_id,
                ie=NexxIE.ie_key(), video_id=nexx_id)

        nexx_id = jwplatform_id = None

        if video_id:
            if re.match(NEXX_ID_RE, video_id):
                return nexx_result(video_id)
            elif re.match(JWPLATFORM_ID_RE, video_id):
                jwplatform_id = video_id

        if not nexx_id:
            display_id = self._match_id(url)
            webpage = self._download_webpage(url, display_id)

            def extract_id(pattern, name, default=NO_DEFAULT):
                return self._html_search_regex(
                    (r'id\s*=\s*["\']video-player["\'][^>]+data-id\s*=\s*["\'](%s)' % pattern,
                     r'\s+id\s*=\s*["\']player_(%s)' % pattern,
                     r'\bdata-id\s*=\s*["\'](%s)' % pattern), webpage, name,
                    default=default)

            nexx_id = extract_id(NEXX_ID_RE, 'nexx id', default=None)
            if nexx_id:
                return nexx_result(nexx_id)

            if not jwplatform_id:
                jwplatform_id = extract_id(JWPLATFORM_ID_RE, 'jwplatform id')

            media = self._download_json(
                'https://cdn.jwplayer.com/v2/media/' + jwplatform_id,
                display_id)
            nexx_id = try_get(
                media, lambda x: x['playlist'][0]['nexx_id'], compat_str)

            if nexx_id:
                return nexx_result(nexx_id)

        return self.url_result(
            'jwplatform:%s' % jwplatform_id, ie=JWPlatformIE.ie_key(),
            video_id=jwplatform_id)

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
        'url': 'https://www.tele5.de/filme/schlefaz-der-polyp-die-bestie-mit-den-todesarmen-ab-13042018/',
        'info_dict': {
            'id': 'XSWj0xbO',
            'ext': 'mp4',
            # fun fact: upload_date is not visible on the web page for this video
            'upload_date': '20200326',  # this is a re-upload
            'timestamp': 1585190811,
            'duration': 8701.0,
            'title': 'SchleFaZ: Der Polyp - Die Bestie mit den Todesarmen (ab 13.04.2018)',
            'description': 'SchleFaZ: Der Polyp - Die Bestie mit den Todesarmen (ab 13.04.2018)'
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.tele5.de/filme/schlefaz-dragon-crusaders/',
        'info_dict': {
            'id': '1F8PHGxn',
            'ext': 'mp4',
            'upload_date': '20190509',
            'timestamp': 1557441600,
            'duration': 8181.0,
            'title': 'SchleFaZ: Dragon Crusaders',
            'description': 'Drachenzähmen schlecht gemacht! Oliver Kalkofe und Peter Rütten knöpfen sich mit "SchleFaZ: Dragon Crusaders" eine wahrhaft verhext-verflixte Drachen-Sause vor. Statt großer Kampf, großer Krampf. Nicht nur in den Füßen, die einem bei dem müden Fantasy-Abenteuer garantiert einschlafen!'
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # TODO: 400 Bad Request error on webpage, remove this test? (they might fix it eventually)
        'url': 'https://www.tele5.de/video-clip/?ve_id=1609440',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/filme/making-of/avengers-endgame/',
        'only_matching': True,
    }, {
        'url': 'https://www.tele5.de/star-trek/raumschiff-voyager/ganze-folge/das-vinculum/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        video_id = (qs.get('vid') or qs.get('ve_id') or [None])[0]

        NEXX_ID_RE = r'\d{6,}'
        JWPLATFORM_ID_RE = r'[a-zA-Z0-9]{8}'

        def nexx_url(nexx_id):
            return 'https://api.nexx.cloud/v3/759/videos/byid/%s' % nexx_id

        def nexx_result(nexx_id):
            return self.url_result(nexx_url(nexx_id), ie=NexxIE.ie_key(), video_id=nexx_id)

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

            if not jwplatform_id:
                jwplatform_id = extract_id(JWPLATFORM_ID_RE, 'jwplatform id')
            nexx_id = extract_id(NEXX_ID_RE, 'nexx id', default=None)
            if nexx_id:
                return nexx_result(nexx_id)

            media = self._download_json(
                'https://cdn.jwplayer.com/v2/media/' + jwplatform_id,
                display_id)

            nexx_id = try_get(
                media, lambda x: x['playlist'][0]['nexx_id'], compat_str)

            # TODO: nexx offers more formats, but fails (404) on some videos
            # if nexx_id:
            #    return nexx_result(nexx_id)

        return self.url_result(
            'jwplatform:%s' % jwplatform_id, ie=JWPlatformIE.ie_key(),
            video_id=jwplatform_id)

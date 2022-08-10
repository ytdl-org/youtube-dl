# coding: utf-8
from __future__ import unicode_literals

import re
from typing import Optional

from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    extract_attributes, RegexNotFoundError,
)

from .dplay import DPlayIE


class Tele5IE(DPlayIE):
    _VALID_URL = r'https?://(?:www\.)?tele5\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _GEO_COUNTRIES = ['DE']
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
        'skip': 'No longer available: "404 Seite nicht gefunden"',
    }, {
        # jwplatform, nexx unavailable
        'url': 'https://www.tele5.de/filme/ghoul-das-geheimnis-des-friedhofmonsters/',
        'info_dict': {
            'id': 'WJuiOlUp',
            'ext': 'mp4',
            'upload_date': '20200603',
            'timestamp': 1591214400,
            'title': 'Ghoul - Das Geheimnis des Friedhofmonsters',
            'description': 'md5:42002af1d887ff3d5b2b3ca1f8137d97',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'No longer available, redirects to Filme page',
    }, {
        'url': 'https://tele5.de/mediathek/angel-of-mine/',
        'info_dict': {
            'id': '1252360',
            'ext': 'mp4',
            'upload_date': '20220109',
            'timestamp': 1641762000,
            'title': 'Angel of Mine',
            'description': 'md5:a72546a175e1286eb3251843a52d1ad7',
        },
        'params': {
            'format': 'bestvideo',
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

    _PLAYER_REGEX = r'(<hyoga-player\b[^>]+?>)'

    def _extract_single_entry(self,
                              player_element: str,
                              url: str) -> Optional[dict]:
        player_info = extract_attributes(player_element)
        asset_id, country, realm = (player_info[x] for x in ('assetid', 'locale', 'realm',))
        endpoint = compat_urlparse.urlparse(player_info['endpoint']).hostname
        source_type = player_info.get('sourcetype')
        if source_type:
            endpoint = '%s-%s' % (source_type, endpoint)
        try:
            return self._get_disco_api_info(url, asset_id, endpoint, realm, country)
        except ExtractorError as e:
            if getattr(e, 'message', '') == 'Missing deviceId in context':
                raise ExtractorError('DRM protected', cause=e, expected=True)
            raise

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player_elements = re.findall(pattern=self._PLAYER_REGEX,
                                     string=webpage)
        if len(player_elements) == 0:
            raise RegexNotFoundError('Unable to extract Player Element {0}'.format(self._PLAYER_REGEX))

        elif len(player_elements) > 1:
            entries = [self._extract_single_entry(player_element=player_element,
                                                  url=url) for player_element in player_elements]
            video_info = {'_type': 'playlist',
                          'entries': entries}
        else:
            video_info = self._extract_single_entry(player_element=player_elements[0], url=url)
        return video_info

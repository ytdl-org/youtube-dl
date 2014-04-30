# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class NRKIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?nrk\.no/(?:video|lyd)/[^/]+/(?P<id>[\dA-F]{16})'

    _TESTS = [
        {
            'url': 'http://www.nrk.no/video/dompap_og_andre_fugler_i_piip_show/D0FA54B5C8B6CE59/emne/piipshow/',
            'md5': 'a6eac35052f3b242bb6bb7f43aed5886',
            'info_dict': {
                'id': '150533',
                'ext': 'flv',
                'title': 'Dompap og andre fugler i Piip-Show',
                'description': 'md5:d9261ba34c43b61c812cb6b0269a5c8f'
            }
        },
        {
            'url': 'http://www.nrk.no/lyd/lyd_av_oppleser_for_blinde/AEFDDD5473BA0198/',
            'md5': '3471f2a51718195164e88f46bf427668',
            'info_dict': {
                'id': '154915',
                'ext': 'flv',
                'title': 'Slik høres internett ut når du er blind',
                'description': 'md5:a621f5cc1bd75c8d5104cb048c6b8568',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id)

        video_id = self._html_search_regex(r'<div class="nrk-video" data-nrk-id="(\d+)">', page, 'video id')

        data = self._download_json(
            'http://v7.psapi.nrk.no/mediaelement/%s' % video_id, video_id, 'Downloading media JSON')

        if data['usageRights']['isGeoBlocked']:
            raise ExtractorError('NRK har ikke rettig-heter til å vise dette programmet utenfor Norge', expected=True)

        video_url = data['mediaUrl'] + '?hdcore=3.1.1&plugin=aasp-3.1.1.69.124'

        images = data.get('images')
        if images:
            thumbnails = images['webImages']
            thumbnails.sort(key=lambda image: image['pixelWidth'])
            thumbnail = thumbnails[-1]['imageUrl']
        else:
            thumbnail = None

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': data['title'],
            'description': data['description'],
            'thumbnail': thumbnail,
        }
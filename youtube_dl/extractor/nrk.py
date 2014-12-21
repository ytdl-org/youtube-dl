# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    unified_strdate,
)


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


class NRKTVIE(InfoExtractor):
    _VALID_URL = r'http://tv\.nrk(?:super)?\.no/(?:serie/[^/]+|program)/(?P<id>[a-zA-Z]{4}\d{8})'

    _TESTS = [
        {
            'url': 'http://tv.nrk.no/serie/20-spoersmaal-tv/MUHH48000314/23-05-2014',
            'md5': '7b96112fbae1faf09a6f9ae1aff6cb84',
            'info_dict': {
                'id': 'MUHH48000314',
                'ext': 'flv',
                'title': '20 spørsmål',
                'description': 'md5:bdea103bc35494c143c6a9acdd84887a',
                'upload_date': '20140523',
                'duration': 1741.52,
            }
        },
        {
            'url': 'http://tv.nrk.no/program/mdfp15000514',
            'md5': 'af01795a31f1cf7265c8657534d8077b',
            'info_dict': {
                'id': 'mdfp15000514',
                'ext': 'flv',
                'title': 'Kunnskapskanalen: Grunnlovsjubiléet - Stor ståhei for ingenting',
                'description': 'md5:654c12511f035aed1e42bdf5db3b206a',
                'upload_date': '20140524',
                'duration': 4605.0,
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id)

        title = self._html_search_meta('title', page, 'title')
        description = self._html_search_meta('description', page, 'description')
        thumbnail = self._html_search_regex(r'data-posterimage="([^"]+)"', page, 'thumbnail', fatal=False)
        upload_date = unified_strdate(self._html_search_meta('rightsfrom', page, 'upload date', fatal=False))
        duration = float_or_none(
            self._html_search_regex(r'data-duration="([^"]+)"', page, 'duration', fatal=False))

        formats = []

        f4m_url = re.search(r'data-media="([^"]+)"', page)
        if f4m_url:
            formats.append({
                'url': f4m_url.group(1) + '?hdcore=3.1.1&plugin=aasp-3.1.1.69.124',
                'format_id': 'f4m',
                'ext': 'flv',
            })

        m3u8_url = re.search(r'data-hls-media="([^"]+)"', page)
        if m3u8_url:
            formats.append({
                'url': m3u8_url.group(1),
                'format_id': 'm3u8',
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
        }

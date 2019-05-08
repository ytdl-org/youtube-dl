# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DBTVIE(InfoExtractor):
    _VALID_URL = r'https://www\.dagbladet\.no/video/[^/]+/(?P<id>[^/]+)/?$'
    _TESTS = [{
        'url': 'https://www.dagbladet.no/video/trailer-our-planet/hdECB3y6',
        'info_dict': {
            'id': 'hdECB3y6',
            'ext': 'mp4',
            'title': 'Trailer: «Our Planet»',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)
        video_id = mobj.group("id")
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        video_url = 'https://content.jwplatform.com/manifests/%s.m3u8' % video_id
        formats = self._extract_m3u8_formats(video_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class DBYTIE(InfoExtractor):
    _VALID_URL = r'https://www\.dagbladet\.no/video/(?P<id>[^/]+)/?$'
    _TESTS = [{
        'url': 'https://www.dagbladet.no/video/-VPqpBpkwDk/',
        'info_dict': {
            'id': '-VPqpBpkwDk',
            'ext': 'mp4',
            'upload_date': '20160916',
            'uploader': 'Dagbladet',
            'description': 'Video originally published on dagbladet.no/dbtv.no on 19.03.2014\n\nTrailer - Børning',
            'uploader_id': 'UCk5pvsyZJoYJBd7_oFPTlRQ',
            'title': 'Børning',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)
        video_id = mobj.group("id")
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)

        return {
            '_type': 'url_transparent',
            'url': 'https://www.youtube.com/watch?v=%s' % video_id,
            'id': video_id,
            'title': title,
        }

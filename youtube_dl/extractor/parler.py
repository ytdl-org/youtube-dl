# coding: utf-8
from __future__ import unicode_literals

from urllib import parse

from .common import InfoExtractor

from ..utils import (
    clean_html,
    strip_or_none,
    unified_timestamp,
    urlencode_postdata,
)


class ParlerIE(InfoExtractor):
    """Extract videos from posts on Parler."""

    _UUID_RE = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    _VALID_URL = r'https://parler\.com/feed/(?P<id>%s)' % (_UUID_RE, )
    _TESTS = [
        {
            'url': 'https://parler.com/feed/df79fdba-07cc-48fe-b085-3293897520d7',
            'md5': '16e0f447bf186bb3cf64de5bbbf4d22d',
            'info_dict': {
                'id': 'df79fdba-07cc-48fe-b085-3293897520d7',
                'ext': 'mp4',
                'title': '@TulsiGabbard-720',
                'description': 'Puberty-blocking procedures promoted by the Biden/Harris Admin are child abuse. The FDA has recently confirmed these hormones/drugs have extremely dangerous side effects, like brain swelling and vision loss.',
                'timestamp': 1659744000,
                'upload_date': '20220806',
                'uploader': 'Tulsi Gabbard',
                'uploader_id': 'TulsiGabbard',
            },
        },
        {
            'url': 'https://parler.com/feed/a7406eb4-91e5-4793-b5e3-ade57a24e287',
            'md5': '11687e2f5bb353682cee338d181422ed',
            'info_dict': {
                'id': 'a7406eb4-91e5-4793-b5e3-ade57a24e287',
                'ext': 'mp4',
                'title': '@BennyJohnson-360',
                'description': 'This man should run for office',
                'timestamp': 1659657600,
                'upload_date': '20220805',
                'uploader': 'Benny Johnson',
                'uploader_id': 'BennyJohnson',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Get data from API
        api_url = 'https://parler.com/open-api/ParleyDetailEndpoint.php'
        payload = urlencode_postdata({'uuid': video_id})
        status = self._download_json(api_url, video_id, data=payload)

        # Pull out video
        url = status['data'][0]['primary']['video_data']['videoSrc']
        # now we know this exists and is a dict
        data = status['data'][0]['primary']

        # Pull out metadata
        description = strip_or_none(clean_html(data.get('full_body')))
        timestamp = unified_timestamp(data.get('date_created'))
        uploader = strip_or_none(data.get('name'))
        uploader_id = strip_or_none(data.get('username'))
        uploader_url = ('https://parler.com/' + uploader_id) if uploader_id else None

        # Keep the file name short so it doesn't exceed filesystem limits
        title = self._generic_title(url)
        if uploader_id:
            title = '@%s-%s' % (uploader_id, title)

        # Return the result
        return {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
        }

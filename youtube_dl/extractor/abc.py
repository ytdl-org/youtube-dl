from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    js_to_json,
    int_or_none,
)


class ABCIE(InfoExtractor):
    IE_NAME = 'abc.net.au'
    _VALID_URL = r'http://www\.abc\.net\.au/news/[^/]+/[^/]+/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.abc.net.au/news/2014-11-05/australia-to-staff-ebola-treatment-centre-in-sierra-leone/5868334',
        'md5': 'cb3dd03b18455a661071ee1e28344d9f',
        'info_dict': {
            'id': '5868334',
            'ext': 'mp4',
            'title': 'Australia to help staff Ebola treatment centre in Sierra Leone',
            'description': 'md5:809ad29c67a05f54eb41f2a105693a67',
        },
    }, {
        'url': 'http://www.abc.net.au/news/2015-08-17/warren-entsch-introduces-same-sex-marriage-bill/6702326',
        'md5': 'db2a5369238b51f9811ad815b69dc086',
        'info_dict': {
            'id': 'NvqvPeNZsHU',
            'ext': 'mp4',
            'upload_date': '20150816',
            'uploader': 'ABC News (Australia)',
            'description': 'Government backbencher Warren Entsch introduces a cross-party sponsored bill to legalise same-sex marriage, saying the bill is designed to promote "an inclusive Australia, not a divided one.". Read more here: http://ab.co/1Mwc6ef',
            'uploader_id': 'NewsOnABC',
            'title': 'Marriage Equality: Warren Entsch introduces same sex marriage bill',
        },
        'add_ie': ['Youtube'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(
            r'inline(?P<type>Video|YouTube)Data\.push\((?P<json_data>[^)]+)\);',
            webpage)
        if mobj is None:
            raise ExtractorError('Unable to extract video urls')

        urls_info = self._parse_json(
            mobj.group('json_data'), video_id, transform_source=js_to_json)

        if not isinstance(urls_info, list):
            urls_info = [urls_info]

        if mobj.group('type') == 'YouTube':
            return self.playlist_result([
                self.url_result(url_info['url']) for url_info in urls_info])

        formats = [{
            'url': url_info['url'],
            'width': int_or_none(url_info.get('width')),
            'height': int_or_none(url_info.get('height')),
            'tbr': int_or_none(url_info.get('bitrate')),
            'filesize': int_or_none(url_info.get('filesize')),
        } for url_info in urls_info]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }

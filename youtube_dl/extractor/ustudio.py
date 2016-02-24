# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class UstudioIE(InfoExtractor):
    IE_NAME = 'uStudio'
    _VALID_URL = r'http://(?:www\.|v1\.)?ustudio.com/video/(?P<id>[\w\d]+)/.+'
    _TESTS = [
        {
            'url': 'http://ustudio.com/video/Uxu2my9bgSph/san_francisco_golden_gate_bridge',
            'md5': '58bbfca62125378742df01fc2abbdef6',
            'info_dict': {
                'id': 'Uxu2my9bgSph',
                'ext': 'mp4',
                'title': 'San Francisco: Golden Gate Bridge',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'md5:23925500697f2c6d4830e387ba51a9be',
                'uploader': 'Tony Farley',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        doc = self._download_xml(
            'http://v1.ustudio.com/embed/{0}/ustudio/config.xml'.format(
                video_id),
            video_id,
            note='Downloading video info',
            errnote='Failed to download video info')

        formats = [
            {
                'url': quality.attrib['url'],
                'width': int_or_none(quality.attrib.get('width')),
                'height': int_or_none(quality.attrib.get('height')),
            } for quality in doc.findall('./qualities/quality/video')
        ]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'uploader': self._html_search_regex(
                r'<a href=".*/user/.+">(.+)</a> on',
                webpage,
                'uploader',
                fatal=False),
        }

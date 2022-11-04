# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse as urlparse,
    compat_parse_qs as qsparse,
    float_or_none,
    str_or_none,
)


class BloggerIE(InfoExtractor):
    IE_NAME = 'blogger.com'
    _VALID_URL = r'https?://(?:www\.)?blogger\.com/video\.g\?token=(?P<id>.+)'
    _VALID_EMBED = r'''<iframe[^>]+src=["']((?:https?:)?//(?:www\.)?blogger\.com/video\.g\?token=[^"']+)["']'''
    _TESTS = [{
        'url': 'https://www.blogger.com/video.g?token=AD6v5dzEe9hfcARr5Hlq1WTkYy6t-fXH3BBahVhGvVHe5szdEUBEloSEDSTA8-b111089KbfWuBvTN7fnbxMtymsHhXAXwVvyzHH4Qch2cfLQdGxKQrrEuFpC1amSl_9GuLWODjPgw',
        'md5': 'f1bc19b6ea1b0fd1d81e84ca9ec467ac',
        'info_dict': {
            'id': 'BLOGGER-video-3c740e3a49197e16-796',
            'ext': 'mp4',
            'title': 'Blogger',
            'thumbnail': r're:^https?://.*',
        }
    }]

    @staticmethod
    def _extract_url(webpage):
        urls = BloggerIE._extract_urls(webpage)
        return urls[0] if urls else None

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(BloggerIE._VALID_EMBED, webpage)

    def _real_extract(self, url):
        token_id = self._match_id(url)
        webpage = self._download_webpage(url, token_id)
        data_json = self._search_regex(
            r'var\s+VIDEO_CONFIG\s*=\s*(\{.*)', webpage, 'JSON data block')
        data_json = data_json.encode('utf-8').decode('unicode_escape')
        data = json.loads(data_json)
        iframe_id = data.get('iframe_id', token_id)
        thumbnail = data.get('thumbnail')
        streams = data['streams']
        formats = [{
            'ext':
                qsparse(
                    urlparse(stream['play_url']).query
                ).get('mime')[0].replace('video/', ''),
            'url': stream['play_url'],
            'format_id': str_or_none(stream.get('format_id')),
        } for stream in streams]

        return {
            'id': iframe_id,
            'title': 'Blogger',
            'formats': formats,
            'thumbnail': thumbnail,
            'duration':
                float_or_none(qsparse(
                    urlparse(streams[0]['play_url']).query
                ).get('dur')[0]),
        }

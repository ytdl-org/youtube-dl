# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_parse_qs
from ..utils import (
    ExtractorError,
    xpath_text,
    clean_html,
)


class OpenClassRoomIE(InfoExtractor):
    _VALID_URL = r'https?://openclassroom\.stanford\.edu/MainFolder/VideoPage\.php\?(?P<query>.*)'
    _TEST = {
        'url': 'http://openclassroom.stanford.edu/MainFolder/VideoPage.php?course=PracticalUnix&video=intro-environment&speed=100',
        'md5': '544a9468546059d4e80d76265b0443b8',
        'info_dict': {
            'id': 'intro-environment',
            'ext': 'mp4',
            'title': 'Intro Environment',
            'description': 'md5:7d57306c8649f814ca00bb80dada600e',
        }
    }
    _URL_TEMPLATE = 'http://openclassroom.stanford.edu/MainFolder/courses/%s/videos/%s'

    def _real_extract(self, url):
        qs = compat_parse_qs(re.match(self._VALID_URL, url).group('query'))
        if not qs.get('course') or not qs.get('video'):
            raise ExtractorError('Unsupported URL', expected=True)
        video_id = qs['video'][0]
        video_doc = self._download_xml(
            self._URL_TEMPLATE % (qs['course'][0], video_id + '.xml'), video_id)
        return {
            'id': video_id,
            'title': xpath_text(video_doc, 'title', 'title', True),
            'url': self._URL_TEMPLATE % (qs['course'][0], xpath_text(
                video_doc, 'videoFile', 'video url', True)),
            'description': clean_html(xpath_text(video_doc, 'text')),
        }

# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json


class SchooltubeIE(InfoExtractor):
    _VALID_URL = r'http?://www.schooltube.com/video/(?P<id>[^/?#]+)[\S\s]*'
    _TEST = {
        'url': 'http://www.schooltube.com/video/9af6bd6815d74ea7948b/Innovation%20Workshop:%20Electronic%20Circuits%20--%20Part%202:%20Inside%20a%20Cell%20Phone',
        'md5': '0ce7f3f50a8b12054c906968d8512a57',
        'info_dict': {
            'id': '9af6bd6815d74ea7948b',
            'ext': 'mp4',
            'title': 'Innovation Workshop: Electronic Circuits -- Part 2: Inside a Cell Phone',
            'description': 'Inside a cell phone is a world of electronics that is highly engineered and complex. Take a closer look inside as we crack open an iPhone® to look at the microchips under an advanced microscope at the National Institute for Standards and Technology.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        jwplayer_data = self._parse_json(
            self._search_regex(
                r'(?s)jwplayer\(\"schooltube-video\"\).setup\((\{.*?\})\)',
                webpage,
                'setup code',
                fatal=False
            ),
            video_id,
            transform_source=js_to_json
        )

        info_dict = self._parse_jwplayer_data(
            jwplayer_data,
            video_id,
            require_title=False
        )

        info_dict.update({
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'keywords': self._html_search_meta('keywords', webpage)
        })

        return info_dict

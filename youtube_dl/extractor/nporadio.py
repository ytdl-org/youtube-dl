# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor


class NPORadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/radio/(?P<id>.*)'
    _TEST = {
        'url': 'http://www.npo.nl/radio/radio-1',
        'info_dict': {
            'id': 'radio-1',
            'ext': 'mp3',
            'title': 'NPO Radio 1',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
                self._html_get_attribute_regex('data-channel'), webpage, 'title')
       
        json_data = json.loads(
                     self._html_search_regex(
                     self._html_get_attribute_regex('data-streams'), webpage, 'data-streams'))
        
        return {
            'id': video_id,
            'title': title,
            'ext': json_data['codec'],
            'url': json_data['url']
        }

    def _html_get_attribute_regex(self, attribute):
        return r'{0}\s*=\s*\'([^\']+)\''.format(attribute)


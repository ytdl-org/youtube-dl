# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CriterionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?criterion\.com/films/(?P<id>[0-9]+)-.+'
    _TEST = {
        'url': 'http://www.criterion.com/films/184-le-samourai',
        'md5': 'bc51beba55685509883a9a7830919ec3',
        'info_dict': {
            'id': '184',
            'ext': 'mp4',
            'title': 'Le Samouraï',
            'description': 'md5:a2b4b116326558149bef81f76dcbb93f',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        final_url = self._search_regex(
            r'so\.addVariable\("videoURL", "(.+?)"\)\;', webpage, 'video url')
        title = self._og_search_title(webpage)
        description = self._html_search_meta('description', webpage)
        thumbnail = self._search_regex(
            r'so\.addVariable\("thumbnailURL", "(.+?)"\)\;',
            webpage, 'thumbnail url')

        return {
            'id': video_id,
            'url': final_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }

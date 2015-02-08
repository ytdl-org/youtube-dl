# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NationalArchivesUkIE(InfoExtractor):
    _VALID_URL = r'https?://media.nationalarchives.gov.uk/index.php/(?P<id>.*)/?'
    _TEST = {
        'url': 'http://media.nationalarchives.gov.uk/index.php/webinar-using-discovery-national-archives-online-catalogue/'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
	youtube_url = re.search(r'https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)(\w*)(&(amp;)?[\w\?=]*)?', webpage)
	print(youtube_url)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
)


class ScreencastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?screencast\.com/t/(?P<id>[a-zA-Z0-9]+)'
    _TESTS = [{
        'url': 'http://www.screencast.com/t/3ZEjQXlT',
        'md5': '917df1c13798a3e96211dd1561fded83',
        'info_dict': {
            'id': '3ZEjQXlT',
            'ext': 'm4v',
            'title': 'Color Measurement with Ocean Optics Spectrometers',
            'description': 'md5:240369cde69d8bed61349a199c5fb153',
            'thumbnail': r're:^https?://.*\.(?:gif|jpg)$',
        }
    }, {
        'url': 'http://www.screencast.com/t/V2uXehPJa1ZI',
        'md5': 'e8e4b375a7660a9e7e35c33973410d34',
        'info_dict': {
            'id': 'V2uXehPJa1ZI',
            'ext': 'mov',
            'title': 'The Amadeus Spectrometer',
            'description': 're:^In this video, our friends at.*To learn more about Amadeus, visit',
            'thumbnail': r're:^https?://.*\.(?:gif|jpg)$',
        }
    }, {
        'url': 'http://www.screencast.com/t/aAB3iowa',
        'md5': 'dedb2734ed00c9755761ccaee88527cd',
        'info_dict': {
            'id': 'aAB3iowa',
            'ext': 'mp4',
            'title': 'Google Earth Export',
            'description': 'Provides a demo of a CommunityViz export to Google Earth, one of the 3D viewing options.',
            'thumbnail': r're:^https?://.*\.(?:gif|jpg)$',
        }
    }, {
        'url': 'http://www.screencast.com/t/X3ddTrYh',
        'md5': '669ee55ff9c51988b4ebc0877cc8b159',
        'info_dict': {
            'id': 'X3ddTrYh',
            'ext': 'wmv',
            'title': 'Toolkit 6 User Group Webinar (2014-03-04) - Default Judgment and First Impression',
            'description': 'md5:7b9f393bc92af02326a5c5889639eab0',
            'thumbnail': r're:^https?://.*\.(?:gif|jpg)$',
        }
    }, {
        'url': 'http://screencast.com/t/aAB3iowa',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_url = self._html_search_regex(
            r'json\+oembed" href="([^"]+)"', webpage,
            'json embed', default=None)
        data = self._download_json(json_url,video_id)
        video_url = data.get('url')
        title = data.get('title') or self._og_search_title(webpage, default=None)
        thumbnail = data.get('thumbnail_url') or self._og_search_thumbnail(webpage, default=None)
        description = self._og_search_description(webpage, default=None)
        if description is None:
            description = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }


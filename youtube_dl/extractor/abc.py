from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class ABCIE(InfoExtractor):
    IE_NAME = 'abc.net.au'
    _VALID_URL = r'http://www\.abc\.net\.au/news/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.abc.net.au/news/2014-11-05/australia-to-staff-ebola-treatment-centre-in-sierra-leone/5868334',
        'md5': 'cb3dd03b18455a661071ee1e28344d9f',
        'info_dict': {
            'id': '5868334',
            'ext': 'mp4',
            'title': 'Australia to help staff Ebola treatment centre in Sierra Leone',
            'description': 'md5:809ad29c67a05f54eb41f2a105693a67',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        urls_info_json = self._search_regex(
            r'inlineVideoData\.push\((.*?)\);', webpage, 'video urls',
            flags=re.DOTALL)
        urls_info = json.loads(urls_info_json.replace('\'', '"'))
        formats = [{
            'url': url_info['url'],
            'width': int(url_info['width']),
            'height': int(url_info['height']),
            'tbr': int(url_info['bitrate']),
            'filesize': int(url_info['filesize']),
        } for url_info in urls_info]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }

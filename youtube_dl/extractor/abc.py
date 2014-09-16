from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class ABCIE(InfoExtractor):
    IE_NAME = 'abc.net.au'
    _VALID_URL = r'http://www\.abc\.net\.au/news/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.abc.net.au/news/2014-07-25/bringing-asylum-seekers-to-australia-would-give/5624716',
        'md5': 'dad6f8ad011a70d9ddf887ce6d5d0742',
        'info_dict': {
            'id': '5624716',
            'ext': 'mp4',
            'title': 'Bringing asylum seekers to Australia would give them right to asylum claims: professor',
            'description': 'md5:ba36fa5e27e5c9251fd929d339aea4af',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
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

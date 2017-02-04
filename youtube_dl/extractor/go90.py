# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import sanitize_url


class Go90IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?go90\.com/profiles/va_(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.go90.com/profiles/va_07d47f43a7b04eb5b693252f2bd1086b',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '07d47f43a7b04eb5b693252f2bd1086b',
            'ext': 'mp4',
            'title': 't@gged | #shotgun | go90',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader_id': '98ac1613c7624a8387596b5d5e441064',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)


        # scrape data from webpage
        page_data = {}
        self.to_screen("Scrape data from webpage")

        video_title = self._html_search_regex(
            r'<title\b[^>]*>\s*(.*)\s*</title>', webpage, 'title')
        self.to_screen("Title: " + video_title)


        # retrieve upLynk url
        video_api = "https://www.go90.com/api/metadata/video/" + video_id
        video_api_data = self._download_json(video_api, video_id)  #TODO: overwrite `note=` to output better explanation
        uplynk_preplay_url = sanitize_url(video_api_data['url'])


        return {
            '_type': 'url_transparent',
            'url': uplynk_preplay_url,
            'id': video_id,
            'title': video_title,
            'ie_key': 'UplynkPreplay',
            # TODO more properties (see youtube_dl/extractor/common.py)
        }

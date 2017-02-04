# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .uplynk import UplynkPreplayIE
from ..utils import sanitize_url


class Go90IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?go90\.com/profiles/va_(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.go90.com/profiles/va_07d47f43a7b04eb5b693252f2bd1086b',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '07d47f43a7b04eb5b693252f2bd1086b',
            'ext': 'mp4',
            'title': 't@gged S1:E1 #shotgun',
            'thumbnail': r're:^https?://.*\.jpg$',
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


        # scrape data from webpage
        page_data = {}
        self.to_screen("Scrape data from webpage")

        page_data['id'] = video_id

        video_title = self._html_search_regex(
            r'<title\b[^>]*>\s*(.*)\s*</title>', webpage, 'title')
        page_data['title'] = video_title
        self.to_screen("Title: " + page_data['title'])


        # retrieve upLynk data
        video_api = "https://www.go90.com/api/metadata/video/" + video_id
        video_api_data = self._download_json(video_api, video_id)  #TODO: overwrite `note=` to output better explanation
        video_token_url = sanitize_url(video_api_data['url'])

        uplynk_preplay = UplynkPreplayIE(self._downloader)
        uplynk_data = uplynk_preplay.extract(video_token_url)


        # merge data
        video_data = uplynk_data.copy()
        video_data.update(page_data)
        # TODO more properties (see youtube_dl/extractor/common.py)

        return video_data

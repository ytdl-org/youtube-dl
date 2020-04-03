from __future__ import unicode_literals

from .common import InfoExtractor




class SonumaIE(InfoExtractor):

    _VALID_URL = r'https://www\.sonuma\.be/archive/\S+'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id
        )

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        download_url = self._html_search_regex(

            r'(https://cdn\.acidcow\.com/pics/[0-9]+/video/\S+\.mp4)',

            webpage, "download_url"
        )
        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }
from __future__ import unicode_literals

from .common import InfoExtractor


class vlareIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?vlare\.tv/v/(?P<id>\w+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id
        )

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        download_url = self._html_search_regex(

            r'((https:\/\/)v\.vlare\.tv/[a-zA-Z0-9]*\.[0-9]*\.mp4)',

            webpage, "download_url"
        )
        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }

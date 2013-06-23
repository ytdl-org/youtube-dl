import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class YouJizzIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?youjizz\.com/videos/(?P<videoid>[^.]+).html$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        video_title = self._html_search_regex(r'<title>(?P<title>.*)</title>',
            webpage, u'title').strip()

        # Get the embed page
        result = re.search(r'https?://www.youjizz.com/videos/embed/(?P<videoid>[0-9]+)', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract embed page')

        embed_page_url = result.group(0).strip()
        video_id = result.group('videoid')

        webpage = self._download_webpage(embed_page_url, video_id)

        # Get the video URL
        video_url = self._search_regex(r'so.addVariable\("file",encodeURIComponent\("(?P<source>[^"]+)"\)\);',
            webpage, u'video URL')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'ext': 'flv',
                'format': 'flv',
                'player_url': embed_page_url}

        return [info]

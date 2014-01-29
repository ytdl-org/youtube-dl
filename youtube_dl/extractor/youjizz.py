from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class YouJizzIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?youjizz\.com/videos/(?P<videoid>[^.]+)\.html$'
    _TEST = {
        'url': 'http://www.youjizz.com/videos/zeichentrick-1-2189178.html',
        'file': '2189178.flv',
        'md5': '07e15fa469ba384c7693fd246905547c',
        'info_dict': {
            "title": "Zeichentrick 1",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        age_limit = self._rta_search(webpage)

        # Get the video title
        video_title = self._html_search_regex(r'<title>(?P<title>.*)</title>',
            webpage, 'title').strip()

        # Get the embed page
        result = re.search(r'https?://www.youjizz.com/videos/embed/(?P<videoid>[0-9]+)', webpage)
        if result is None:
            raise ExtractorError('ERROR: unable to extract embed page')

        embed_page_url = result.group(0).strip()
        video_id = result.group('videoid')

        webpage = self._download_webpage(embed_page_url, video_id)

        # Get the video URL
        m_playlist = re.search(r'so.addVariable\("playlist", ?"(?P<playlist>.+?)"\);', webpage)
        if m_playlist is not None:
            playlist_url = m_playlist.group('playlist')
            playlist_page = self._download_webpage(playlist_url, video_id,
                                                   'Downloading playlist page')
            m_levels = list(re.finditer(r'<level bitrate="(\d+?)" file="(.*?)"', playlist_page))
            if len(m_levels) == 0:
                raise ExtractorError('Unable to extract video url')
            videos = [(int(m.group(1)), m.group(2)) for m in m_levels]
            (_, video_url) = sorted(videos)[0]
            video_url = video_url.replace('%252F', '%2F')
        else:
            video_url = self._search_regex(r'so.addVariable\("file",encodeURIComponent\("(?P<source>[^"]+)"\)\);',
                                           webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': 'flv',
            'format': 'flv',
            'player_url': embed_page_url,
            'age_limit': age_limit,
        }

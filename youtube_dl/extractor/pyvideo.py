from __future__ import unicode_literals

import re
import os

from .common import InfoExtractor


class PyvideoIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?pyvideo\.org/video/(?P<id>\d+)/(.*)'

    _TESTS = [
        {
            'url': 'http://pyvideo.org/video/1737/become-a-logging-expert-in-30-minutes',
            'md5': 'de317418c8bc76b1fd8633e4f32acbc6',
            'info_dict': {
                'id': '24_4WWkSmNo',
                'ext': 'mp4',
                'title': 'Become a logging expert in 30 minutes',
                'description': 'md5:9665350d466c67fb5b1598de379021f7',
                'upload_date': '20130320',
                'uploader': 'NextDayVideo',
                'uploader_id': 'NextDayVideo',
            },
            'add_ie': ['Youtube'],
        },
        {
            'url': 'http://pyvideo.org/video/2542/gloriajw-spotifywitherikbernhardsson182m4v',
            'md5': '5fe1c7e0a8aa5570330784c847ff6d12',
            'info_dict': {
                'id': '2542',
                'ext': 'm4v',
                'title': 'Gloriajw-SpotifyWithErikBernhardsson182',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        m_youtube = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', webpage)
        if m_youtube is not None:
            return self.url_result(m_youtube.group(1), 'Youtube')

        title = self._html_search_regex(
            r'<div class="section">\s*<h3(?:\s+class="[^"]*"[^>]*)?>([^>]+?)</h3>',
            webpage, 'title', flags=re.DOTALL)
        video_url = self._search_regex(
            [r'<source src="(.*?)"', r'<dt>Download</dt>.*?<a href="(.+?)"'],
            webpage, 'video url', flags=re.DOTALL)

        return {
            'id': video_id,
            'title': os.path.splitext(title)[0],
            'url': video_url,
        }

from __future__ import unicode_literals

from .common import InfoExtractor
from .streamtape import StreamtapeIE
from ..utils import (
    escape_url
)


class MyVidsterIE(InfoExtractor):
    IE_NAME = 'myvidster'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/video/(?P<id>\d+)/'

    _TEST = {
        'url': 'http://www.myvidster.com/video/32059805/Hot_chemistry_with_raw_love_making',
        'md5': '95296d0231c1363222c3441af62dc4ca',
        'info_dict': {
            'id': '3685814',
            'title': 'md5:7d8427d6d02c4fbcef50fe269980c749',
            'upload_date': '20141027',
            'uploader': 'utkualp',
            'ext': 'mp4',
            'age_limit': 18,
        },
        'add_ie': ['XHamster'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        streamtape_url = StreamtapeIE._extract_url(webpage)
        print(f"streamtape url: {streamtape_url}")
        if streamtape_url:
            
            entry_video = StreamtapeIE._extract_info_video(streamtape_url, video_id)
            print(entry_video)
            entry_video['title'] = title
            print(entry_video)
         
            return entry_video

        real_url = self._html_search_regex(r'rel="videolink" href="(?P<real_url>.*)">',
            webpage, 'real video url')
        
        self.to_screen(f"{video_id}:{title}:{real_url}:{escape_url(real_url)}")
        entry_video = self.url_result(escape_url(real_url), None, video_id, title)
        self.to_screen(f"Entry video: {entry_video}")
        
        return entry_video

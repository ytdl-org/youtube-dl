# encoding: utf-8
import re

from .common import InfoExtractor

class XboxClipsIE(InfoExtractor):
    _VALID_URL = r'^https?://(www\.)?xboxclips\.com/video.php\?.*vid=(?P<id>[\w-]*)'
    _TEST = {
            'url': 'https://xboxclips.com/video.php?uid=2533274823424419&gamertag=Iabdulelah&vid=074a69a9-5faf-46aa-b93b-9909c1720325',
            'md5': 'fbe1ec805e920aeb8eced3c3e657df5d',
            'info_dict': {
                'id': '074a69a9-5faf-46aa-b93b-9909c1720325',
                'ext': 'mp4',
                'title': 'Iabdulelah playing Upload Studio',
                }
            } 

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(r'Link.*?"(.*?)"',
                webpage, 'video URL')

        video_title = self._html_search_regex(r'<title>.*?\|(.*?)<',
                webpage, 'title')

        return {
                'id': video_id,
                'url': video_url,
                'title': video_title,
                'ext': 'mp4',
                }

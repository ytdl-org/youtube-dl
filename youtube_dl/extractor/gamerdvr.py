# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GamerDVRIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamerdvr\.com/gamer/\S+/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://gamerdvr.com/gamer/videogamer3/video/83193307',
        'md5': 'f747c74fbc7617a70d8c071927623cde',
        'info_dict': {
            'id': '83193307',
            'ext': 'mp4',
            'title': "videogamer3's Xbox Call of Duty®: Modern Warfare® clip 83193307. Find your Xbox clips on GamerDVR.com",
            'description': "videogamer3's Xbox Call of Duty®: Modern Warfare® clips and gameplay playing Call of Duty®: Modern Warfare®. All your Xbox clips and screenshots on GamerDVR.com. View, manage, and share easily!",
            'uploader': 'videogamer3'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r"<source src=\"(\S+)\"", webpage, 'URL')
        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title', fatal=False)
        description = self._html_search_regex(
            r"<meta name=\"description\" content=([\"'])((?:\\\1|.)*?)\1",
            webpage, 'description', group=2, fatal=False)
        uploader = self._html_search_regex(
            r"window\.gamertag = '(.+)';", webpage, 'uploader', fatal=False)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': video_url
        }

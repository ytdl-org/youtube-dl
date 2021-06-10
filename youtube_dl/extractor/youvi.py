from __future__ import unicode_literals
from .youtube import YoutubeIE
from .common import InfoExtractor


class YouviIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youvi\.ru/post/(?P<id>[A-Za-z0-9]+)'
    _TEST = {
        'url': "https://youvi.ru/post/oZMXbu5sRoN",
        'md5': "b6d7e74265a8e05ebbfafeb98d204ffa",
        'info_dict': {
            'id': 'oZMXbu5sRoN',
            'ext': 'mp4',
            'title': 'Теперь Дворец Путина есть в Minecraft в масштабе 1 к 1',
        },
        'params': {
            'skip_download': True,
        },
    }

    @staticmethod
    def findYoutube(webpage):
        res = ""
        if webpage.find('external_id:') == -1:
            return None
        pointer = webpage.find('external_id:') + 13
        while webpage[pointer] != '\"':
            res += webpage[pointer]
            pointer += 1
        return res

    @staticmethod
    def findVideo(webpage):
        res = ""
        pointer = webpage.find('source_file:') + 18
        while webpage[pointer] != '\"':
            res += webpage[pointer]
            pointer += 1
        return res

    @staticmethod
    def findTitle(webpage):
        start = webpage.find('<title>') + 7
        end = webpage.find('</title>')
        res = webpage[start:end]
        realend = res.find('. — Youvi')
        if realend != -1:
            return res[0:realend]
        return res

    def _real_extract(self, url):
        post_id = self._match_id(url)
        webpage = self._download_webpage(url, post_id)
        title = self.findTitle(webpage)

        if self.findYoutube(webpage):
            youtube_url = "https://www.youtube.com/watch?v=" + self.findYoutube(webpage)
            return self.url_result(youtube_url, ie=YoutubeIE.ie_key())

        video_url = self.findVideo(webpage).encode().decode('unicode-escape')

        return {
            'id': post_id,
            'title': title,
            'url': video_url
        }

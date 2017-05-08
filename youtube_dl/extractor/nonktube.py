# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class NonkTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nonktube\.com\/video/(?P<id>[0-9]+)/[0-9a-zA-Z\-]*'
    _TESTS = [{
        'url': 'https://www.nonktube.com/video/118636/sensual-wife-uncensored-fucked-in-hairy-pussy-and-facialized',
        'md5': 'ccd2df2aef9f44e51773c8ea59de6fd1',
        'info_dict': {
            'id': '118636',
            'ext': 'mp4',
            'title': 'Sensual Wife Uncensored Fucked In Hairy Pussy And Facialized',
            'thumbnail': 'https://www.nonktube.com/media/videos/tmb_2/118636/default.jpg',
            'uploader': 'https://www.nonktube.com/user/cumdrinkingwife',
            'age_limit': 18
        }
    }, {
        'url': 'https://www.nonktube.com/video/118698/2-japanese-girls-sharing-one-dick-uncesnored',
        'md5': 'bb4bdd0a61f591e2f5f7429dc860327e',
        'info_dict': {
            'id': '118698',
            'ext': 'mp4',
            'title': '2 Japanese Girls Sharing One Dick Uncesnored',
            'thumbnail': 'https://www.nonktube.com/media/videos/tmb_2/118698/default.jpg',
            'uploader': 'https://www.nonktube.com/user/cumdrinkingwife',
            'age_limit': 18
        }
    }]
    DOWNLOAD_URL_TEMPLATE = 'https://cdn.nonktube.com/%s.mp4'
    UPLOADER_URL_TEMPLATE = 'https://www.nonktube.com/user/%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self.DOWNLOAD_URL_TEMPLATE % str(video_id)

        title = self._html_search_regex(
            [r'<title>(?P<title>.+?) - NonkTube.com</title>',
             r'<h1 class=.*>(?P<title>.+?)</h1>'], webpage, 'title', group='title')

        thumbnail = self._html_search_regex(
            [r'<img src="(?P<thumbnail>.+?)" title="' + re.escape(title) + r'" alt="' + re.escape(title) + r'" width="[0-9]*" height="[0-9]*" />'],
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        # only one link of format /user/ is present in every video which gives the uploader username
        uploader = self._html_search_regex(
            [r'<a href="/user/(?P<uploader_id>[0-9A-Za-z]+?)">'],
            webpage, 'uploader', fatal=False, group='uploader_id')
        if uploader is not None:
            uploader = self.UPLOADER_URL_TEMPLATE % uploader

        age_limit = 18

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'url': video_url,
            'age_limit': age_limit,
            'ext': 'mp4',
        }

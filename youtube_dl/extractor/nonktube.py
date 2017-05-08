# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class NonkTubeIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?nonktube\.com\/video\/(?P<id>[0-9]+)\/[0-9a-zA-Z\-]*'
    _TESTS = [{
        'url': 'https://www.nonktube.com/video/118636/sensual-wife-uncensored-fucked-in-hairy-pussy-and-facialized',
        'md5': 'ccd2df2aef9f44e51773c8ea59de6fd1',
        'info_dict': {
            'id': '118636',
            'ext': 'mp4',
            'title': 'Sensual Wife Uncensored Fucked In Hairy Pussy And Facialized',
            'thumbnail': 'https://www.nonktube.com/media/videos/tmb_2/118636/default.jpg',
        }
    }, {
        'url': 'https://www.nonktube.com/video/118698/2-japanese-girls-sharing-one-dick-uncesnored',
        'md5': 'bb4bdd0a61f591e2f5f7429dc860327e',
        'info_dict': {
            'id': '118698',
            'ext': 'mp4',
            'title': '2 Japanese Girls Sharing One Dick Uncesnored',
            'thumbnail': 'https://www.nonktube.com/media/videos/tmb_2/118698/default.jpg',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            [r'<title>(.+?)(?: - NonkTube.com)</title>'],
            webpage, 'title')

        thumbnail = self._html_search_regex(
            [r'<img src="(.+?)(?:" title="' + re.escape(title) + r'" alt="' + re.escape(title) + r'" width="160" height="120" />)'],
            webpage, 'thumbnail', fatal=False)

        video_download_url = "https://cdn.nonktube.com/" + video_id + ".mp4"

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'url': video_download_url,
            'ext': 'mp4',
        }

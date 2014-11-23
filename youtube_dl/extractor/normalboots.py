# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    unified_strdate,
)


class NormalbootsIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?normalboots\.com/video/(?P<videoid>[0-9a-z-]*)/?$'
    _TEST = {
        'url': 'http://normalboots.com/video/home-alone-games-jontron/',
        'md5': '8bf6de238915dd501105b44ef5f1e0f6',
        'info_dict': {
            'id': 'home-alone-games-jontron',
            'ext': 'mp4',
            'title': 'Home Alone Games - JonTron - NormalBoots',
            'description': 'Jon is late for Christmas. Typical. Thanks to: Paul Ritchey for Co-Writing/Filming: http://www.youtube.com/user/ContinueShow Michael Azzi for Christmas Intro Animation: http://michafrar.tumblr.com/ Jerrod Waters for Christmas Intro Music: http://www.youtube.com/user/xXJerryTerryXx Casey Ormond for ‘Tense Battle Theme’:\xa0http://www.youtube.com/Kiamet/',
            'uploader': 'JonTron',
            'upload_date': '20140125',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)
        video_uploader = self._html_search_regex(r'Posted\sby\s<a\shref="[A-Za-z0-9/]*">(?P<uploader>[A-Za-z]*)\s</a>',
                                                 webpage, 'uploader')
        raw_upload_date = self._html_search_regex('<span style="text-transform:uppercase; font-size:inherit;">[A-Za-z]+, (?P<date>.*)</span>',
                                                  webpage, 'date')
        video_upload_date = unified_strdate(raw_upload_date)

        player_url = self._html_search_regex(r'<iframe\swidth="[0-9]+"\sheight="[0-9]+"\ssrc="(?P<url>[\S]+)"', webpage, 'url')
        player_page = self._download_webpage(player_url, video_id)
        video_url = self._html_search_regex(r"file:\s'(?P<file>[^']+\.mp4)'", player_page, 'file')

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': video_uploader,
            'upload_date': video_upload_date,
        }

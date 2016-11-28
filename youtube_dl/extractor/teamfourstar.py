# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .jwplatform import JWPlatformIE
from ..utils import unified_strdate


class TeamFourStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?teamfourstar\.com/(?P<id>[a-z0-9\-]+)/?'
    _TEST = {
        'url': 'http://teamfourstar.com/tfs-abridged-parody-episode-1-2/',
        'info_dict': {
            'id': '0WdZO31W',
            'title': 'TFS Abridged Parody Episode 1',
            'description': 'Episode 1: The Return of Raditz! … Wait…\nCast\nMasakoX – Goku, Roshi\nLanipator – Piccolo, Radditz, Krillin, Vegeta\nVegeta3986 – Radditz, Yamcha, Oolong, Gohan\nHbi2k – Farmer with Shotgun\nMegami33 – Bulma, Puar\nTakahata101 – Nappa\nKaiserNeko – SpacePod\nSongs\nMorgenstemning by Edvard Hagerup Grieg\nCha-La-Head-Cha-La by Kageyama Hiranobu\nWE DO NOT OWN DRAGONBALL. DragonBall is Owned by TOEI ANIMATION, Ltd. and Licensed by FUNimation Productions, Ltd.. All Rights Reserved. DragonBall, DragonBall Z, DragonBall GT and all logos, character names and distinctive likenesses thereof are trademarks of TOEI ANIMATION, Ltd.\nThis is nothing more than a Parody made for entertainment purposes only.',            
            'ext': 'mp4',
            'timestamp': 1394168400,
            'upload_date': '20080508',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        jwplatform_url = JWPlatformIE._extract_url(webpage)

        video_title = self._html_search_regex(
            r'<h1 class="entry-title">(?P<title>.+?)</h1>',
            webpage, 'title')
        video_date = unified_strdate(self._html_search_regex(
            r'<span class="meta-date date updated">(?P<date>.+?)</span>',
            webpage, 'date', fatal=False))
        video_description = self._html_search_regex(
            r'(?s)<div class="content-inner">.*?(?P<description><p>.+?)</div>',
            webpage, 'description', fatal=False)
        video_thumbnail = self._og_search_thumbnail(webpage)

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'title': video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
            'url': jwplatform_url,
        }

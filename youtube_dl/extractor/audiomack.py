# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from ..utils import ExtractorError

import time


class AudiomackIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/song/(?P<id>[\w/-]+)'
    IE_NAME = 'audiomack'
    _TESTS = [
        # hosted on audiomack
        {
            'url': 'http://www.audiomack.com/song/roosh-williams/extraordinary',
            'info_dict':
            {
                'id': 'roosh-williams/extraordinary',
                'ext': 'mp3',
                'title': 'Roosh Williams - Extraordinary'
            }
        },
        # hosted on soundcloud via audiomack
        {
            'add_ie': ['Soundcloud'],
            'url': 'http://www.audiomack.com/song/xclusiveszone/take-kare',
            'info_dict': {
                'id': '172419696',
                'ext': 'mp3',
                'description': 'md5:1fc3272ed7a635cce5be1568c2822997',
                'title': 'Young Thug ft Lil Wayne - Take Kare',
                'uploader': 'Young Thug World',
                'upload_date': '20141016',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_response = self._download_json(
            "http://www.audiomack.com/api/music/url/song/%s?_=%d" % (
                video_id, time.time()),
            video_id)

        if "url" not in api_response:
            raise ExtractorError("Unable to deduce api url of song")
        realurl = api_response["url"]

        # Audiomack wraps a lot of soundcloud tracks in their branded wrapper
        # - if so, pass the work off to the soundcloud extractor
        if SoundcloudIE.suitable(realurl):
            return {'_type': 'url', 'url': realurl, 'ie_key': 'Soundcloud'}

        webpage = self._download_webpage(url, video_id)
        artist = self._html_search_regex(
            r'<span class="artist">(.*?)</span>', webpage, "artist")
        songtitle = self._html_search_regex(
            r'<h1 class="profile-title song-title"><span class="artist">.*?</span>(.*?)</h1>',
            webpage, "title")
        title = artist + " - " + songtitle

        return {
            'id': video_id,
            'title': title,
            'url': realurl,
        }

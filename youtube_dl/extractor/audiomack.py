# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from ..utils import ExtractorError
import datetime
import time


class AudiomackIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/song/(?P<id>[\w/-]+)'
    IE_NAME = 'audiomack'
    _TESTS = [
        #hosted on audiomack
        {
            'url': 'http://www.audiomack.com/song/roosh-williams/extraordinary',
            'info_dict':
            {
                'id' : 'roosh-williams/extraordinary',
                'ext': 'mp3',
                'title': 'Roosh Williams - Extraordinary'
            }
        },
        #hosted on soundcloud via audiomack
        {
            'url': 'http://www.audiomack.com/song/xclusiveszone/take-kare',
            'file': '172419696.mp3',
            'info_dict':
            {
                'ext': 'mp3',
                'title': 'Young Thug ft Lil Wayne - Take Kare',
                "upload_date": "20141016",
                "description": "New track produced by London On Da Track called “Take Kare\"\n\nhttp://instagram.com/theyoungthugworld\nhttps://www.facebook.com/ThuggerThuggerCashMoney\n",
                "uploader": "Young Thug World"
            }
        }
    ]

    def _real_extract(self, url):
        #id is what follows /song/ in url, usually the uploader name + title
        id = self._match_id(url)

        #Call the api, which gives us a json doc with the real url inside
        rightnow = int(time.time())
        apiresponse = self._download_json("http://www.audiomack.com/api/music/url/song/"+id+"?_="+str(rightnow), id)

        if "url" not in apiresponse:
            raise ExtractorError("Unable to deduce api url of song")
        realurl = apiresponse["url"]

        #Audiomack wraps a lot of soundcloud tracks in their branded wrapper
        # - if so, pass the work off to the soundcloud extractor
        if SoundcloudIE.suitable(realurl):
            sc = SoundcloudIE(downloader=self._downloader)
            return sc._real_extract(realurl)
        else:
            #Pull out metadata
            page = self._download_webpage(url, id)
            artist = self._html_search_regex(r'<span class="artist">(.*)</span>', page, "artist")
            songtitle = self._html_search_regex(r'<h1 class="profile-title song-title"><span class="artist">.*</span>(.*)</h1>', page, "title")
            title = artist+" - "+songtitle
            return {
                'id': id,  # ignore id, which is not useful in song name
                'title': title,
                'url': realurl,
                'ext': 'mp3'
            }

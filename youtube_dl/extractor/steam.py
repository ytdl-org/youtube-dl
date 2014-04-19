from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class SteamIE(InfoExtractor):
    _VALID_URL = r"""(?x)http://store\.steampowered\.com/
                (agecheck/)?
                (?P<urltype>video|app)/ #If the page is only for videos or for a game
                (?P<gameID>\d+)/?
                (?P<videoID>\d*)(?P<extra>\??) #For urltype == video we sometimes get the videoID
                """
    _VIDEO_PAGE_TEMPLATE = 'http://store.steampowered.com/video/%s/'
    _AGECHECK_TEMPLATE = 'http://store.steampowered.com/agecheck/video/%s/?snr=1_agecheck_agecheck__age-gate&ageDay=1&ageMonth=January&ageYear=1970'
    _TEST = {
        "url": "http://store.steampowered.com/video/105600/",
        "playlist": [
            {
                "md5": "f870007cee7065d7c76b88f0a45ecc07",
                "info_dict": {
                    'id': '81300',
                    'ext': 'flv',
                    "title": "Terraria 1.1 Trailer",
                    'playlist_index': 1,
                }
            },
            {
                "md5": "61aaf31a5c5c3041afb58fb83cbb5751",
                "info_dict": {
                    'id': '80859',
                    'ext': 'flv',
                    "title": "Terraria Trailer",
                    'playlist_index': 2,
                }
            }
        ],
        'params': {
            'playlistend': 2,
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url, re.VERBOSE)
        gameID = m.group('gameID')

        videourl = self._VIDEO_PAGE_TEMPLATE % gameID
        webpage = self._download_webpage(videourl, gameID)

        if re.search('<h2>Please enter your birth date to continue:</h2>', webpage) is not None:
            videourl = self._AGECHECK_TEMPLATE % gameID
            self.report_age_confirmation()
            webpage = self._download_webpage(videourl, gameID)

        self.report_extraction(gameID)
        game_title = self._html_search_regex(r'<h2 class="pageheader">(.*?)</h2>',
                                             webpage, 'game title')

        mweb = re.finditer(
            r"'movie_(?P<videoID>\d+)': \{\s*FILENAME: \"(?P<videoURL>[\w:/\.\?=]+)\"(,\s*MOVIE_NAME: \"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},",
            webpage)
        titles = re.finditer(
            r'<span class="title">(?P<videoName>.+?)</span>', webpage)
        thumbs = re.finditer(
            r'<img class="movie_thumb" src="(?P<thumbnail>.+?)">', webpage)
        videos = []
        for vid, vtitle, thumb in zip(mweb, titles, thumbs):
            video_id = vid.group('videoID')
            title = vtitle.group('videoName')
            video_url = vid.group('videoURL')
            video_thumb = thumb.group('thumbnail')
            if not video_url:
                raise ExtractorError('Cannot find video url for %s' % video_id)
            videos.append({
                'id': video_id,
                'url': video_url,
                'ext': 'flv',
                'title': unescapeHTML(title),
                'thumbnail': video_thumb
            })
        return self.playlist_result(videos, gameID, game_title)

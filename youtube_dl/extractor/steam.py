import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class SteamIE(InfoExtractor):
    _VALID_URL = r"""http://store\.steampowered\.com/
                (agecheck/)?
                (?P<urltype>video|app)/ #If the page is only for videos or for a game
                (?P<gameID>\d+)/?
                (?P<videoID>\d*)(?P<extra>\??) #For urltype == video we sometimes get the videoID
                """
    _VIDEO_PAGE_TEMPLATE = 'http://store.steampowered.com/video/%s/'
    _AGECHECK_TEMPLATE = 'http://store.steampowered.com/agecheck/video/%s/?snr=1_agecheck_agecheck__age-gate&ageDay=1&ageMonth=January&ageYear=1970'
    _TEST = {
        u"url": u"http://store.steampowered.com/video/105600/",
        u"playlist": [
            {
                u"file": u"81300.flv",
                u"md5": u"f870007cee7065d7c76b88f0a45ecc07",
                u"info_dict": {
                        u"title": u"Terraria 1.1 Trailer",
                        u'playlist_index': 1,
                }
            },
            {
                u"file": u"80859.flv",
                u"md5": u"61aaf31a5c5c3041afb58fb83cbb5751",
                u"info_dict": {
                    u"title": u"Terraria Trailer",
                    u'playlist_index': 2,
                }
            }
        ]
    }


    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

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

        urlRE = r"'movie_(?P<videoID>\d+)': \{\s*FILENAME: \"(?P<videoURL>[\w:/\.\?=]+)\"(,\s*MOVIE_NAME: \"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},"
        mweb = re.finditer(urlRE, webpage)
        namesRE = r'<span class="title">(?P<videoName>.+?)</span>'
        titles = re.finditer(namesRE, webpage)
        thumbsRE = r'<img class="movie_thumb" src="(?P<thumbnail>.+?)">'
        thumbs = re.finditer(thumbsRE, webpage)
        videos = []
        for vid,vtitle,thumb in zip(mweb,titles,thumbs):
            video_id = vid.group('videoID')
            title = vtitle.group('videoName')
            video_url = vid.group('videoURL')
            video_thumb = thumb.group('thumbnail')
            if not video_url:
                raise ExtractorError(u'Cannot find video url for %s' % video_id)
            info = {
                'id':video_id,
                'url':video_url,
                'ext': 'flv',
                'title': unescapeHTML(title),
                'thumbnail': video_thumb
                  }
            videos.append(info)
        return [self.playlist_result(videos, gameID, game_title)]

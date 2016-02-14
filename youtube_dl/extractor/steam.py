from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class SteamIE(InfoExtractor):
    _VALID_URL = r"""(?x)
        https?://store\.steampowered\.com/
            (agecheck/)?
            (?P<urltype>video|app)/ #If the page is only for videos or for a game
            (?P<gameID>\d+)/?
            (?P<videoID>\d*)(?P<extra>\??) # For urltype == video we sometimes get the videoID
        |
        https?://(?:www\.)?steamcommunity\.com/sharedfiles/filedetails/\?id=(?P<fileID>[0-9]+)
    """
    _VIDEO_PAGE_TEMPLATE = 'http://store.steampowered.com/video/%s/'
    _AGECHECK_TEMPLATE = 'http://store.steampowered.com/agecheck/video/%s/?snr=1_agecheck_agecheck__age-gate&ageDay=1&ageMonth=January&ageYear=1970'
    _TESTS = [{
        'url': 'http://store.steampowered.com/video/105600/',
        'playlist': [
            {
                'md5': 'f870007cee7065d7c76b88f0a45ecc07',
                'info_dict': {
                    'id': '81300',
                    'ext': 'flv',
                    'title': 'Terraria 1.1 Trailer',
                    'playlist_index': 1,
                }
            },
            {
                'md5': '61aaf31a5c5c3041afb58fb83cbb5751',
                'info_dict': {
                    'id': '80859',
                    'ext': 'flv',
                    'title': 'Terraria Trailer',
                    'playlist_index': 2,
                }
            }
        ],
        'params': {
            'playlistend': 2,
        }
    }, {
        'url': 'http://steamcommunity.com/sharedfiles/filedetails/?id=242472205',
        'info_dict': {
            'id': 'WB5DvDOOvAY',
            'ext': 'mp4',
            'upload_date': '20140329',
            'title': 'FRONTIERS - Final Greenlight Trailer',
            'description': 'md5:dc96a773669d0ca1b36c13c1f30250d9',
            'uploader': 'AAD Productions',
            'uploader_id': 'AtomicAgeDogGames',
        }
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        fileID = m.group('fileID')
        if fileID:
            videourl = url
            playlist_id = fileID
        else:
            gameID = m.group('gameID')
            playlist_id = gameID
            videourl = self._VIDEO_PAGE_TEMPLATE % playlist_id
        webpage = self._download_webpage(videourl, playlist_id)

        if re.search('<h2>Please enter your birth date to continue:</h2>', webpage) is not None:
            videourl = self._AGECHECK_TEMPLATE % playlist_id
            self.report_age_confirmation()
            webpage = self._download_webpage(videourl, playlist_id)

        if fileID:
            playlist_title = self._html_search_regex(
                r'<div class="workshopItemTitle">(.+)</div>', webpage, 'title')
            mweb = re.finditer(r'''(?x)
                'movie_(?P<videoID>[0-9]+)':\s*\{\s*
                YOUTUBE_VIDEO_ID:\s*"(?P<youtube_id>[^"]+)",
                ''', webpage)
            videos = [{
                '_type': 'url',
                'url': vid.group('youtube_id'),
                'ie_key': 'Youtube',
            } for vid in mweb]
        else:
            playlist_title = self._html_search_regex(
                r'<h2 class="pageheader">(.*?)</h2>', webpage, 'game title')

            mweb = re.finditer(r'''(?x)
                'movie_(?P<videoID>[0-9]+)':\s*\{\s*
                FILENAME:\s*"(?P<videoURL>[\w:/\.\?=]+)"
                (,\s*MOVIE_NAME:\s*\"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},
                ''', webpage)
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
        if not videos:
            raise ExtractorError('Could not find any videos')

        return self.playlist_result(videos, playlist_id, playlist_title)

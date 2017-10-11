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
        'md5': '644c51b580f57db647da083be97c68c8',
        'info_dict': {
                    'id': '2040428',
                    'ext': 'flv',
                    'title': 'Terraria+1.3+Trailer',
                    'playlist_index': 1,
        },
        'params': {
            'playlistend': 1,
        }
    }, {
        'url': 'http://steamcommunity.com/sharedfiles/filedetails/?id=242472205',
        'info_dict': {
            'id': 'X8kpJBlzD2E',
            'ext': 'mp4',
            'upload_date': '20140617',
            'title': 'FRONTIERS - Trapping',
            'description': 'md5:bf6f7f773def614054089e5769c12a6e',
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
                r'<div class="apphub_AppName">(.*?)</div>', webpage, 'game title')
            mweb = re.finditer(r'''(?x)
                'movie_(?P<videoID>[0-9]+)':\s*\{\s*
                FILENAME:\s*"(?P<videoURL>[\w:/\.\?=]+)"
                (,\s*MOVIE_NAME:\s*\"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},
                ''', webpage)
            thumbs = re.finditer(
                r'<img class="movie_thumb" src="(?P<thumbnail>.+?)">', webpage)
            videos = []

            for vid, thumb in zip(mweb, thumbs):
                video_id = vid.group('videoID')
                title = vid.group('videoName')
                video_url = vid.group('videoURL')
                video_thumb = thumb.group('thumbnail')
                if not video_url:
                    raise ExtractorError('Cannot find video url for %s' % video_id)
                videos.append({
                    'id': video_id,
                    'url': video_url,
                    'ext': 'flv',
                    'title': title,
                    'thumbnail': video_thumb
                })
        if not videos:
            raise ExtractorError('Could not find any videos')

        return self.playlist_result(videos, playlist_id, playlist_title)

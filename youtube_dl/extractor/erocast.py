# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import traverse_obj

import re


class ErocastIE(InfoExtractor):
    IE_NAME = 'erocast'
    _VALID_URL = r'https?://(?:www\.)?erocast\.me/track/(?P<id>[0-9]+)/(?P<display_id>[0-9a-zA-Z_-]+)'
    _TESTS = [{
        'url': 'https://erocast.me/track/6508/piano-sample-by-ytdl',
        'md5': '6764726b2d19161e93c9cf3a9a69800a',
        'info_dict': {
            'id': '6508',
            'ext': 'mp4',
            'title': 'Piano sample by ytdl',
            'uploader': 'ytdl',
        }
    }, {
        'url': 'https://erocast.me/track/4254/intimate-morning-with-your-wife',
        'md5': '45b06c21cf93612dd72a3d764c0bb362',
        'info_dict': {
            'id': '4254',
            'ext': 'mp4',
            'title': 'Intimate morning  with your wife',
            'uploader': 'ZLOY_ASMR',
        }
    }, {
        'url': 'https://erocast.me/playlist/2278/rough-hot-and-dirty',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # The Song data is in a script tag with the following format:
        # (see https://github.com/ytdl-org/youtube-dl/issues/31203#issuecomment-1259867716)
        searchPattern = r'<script\b[^>]*>var\s+song_data_%s\s*=\s*(.+?)</script>' % re.escape(video_id)
        jsonString = self._html_search_regex(searchPattern, webpage, 'song_data')

        # The data is in JSON format, so we convert the JSON String to a python object
        # and read the data from this json object
        jsonObject = self._parse_json(jsonString, None, fatal=False)
        audio_url = jsonObject['stream_url']
        title = jsonObject['title']
        user_name = traverse_obj(jsonObject, ('user', 'name'), expected_type=lambda x: x.strip() or None)

        # The audio url is a m3u8 playlist, so we extract the audio url from this playlist
        formats = self._extract_m3u8_formats(
            audio_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls', fatal=False)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'uploader': user_name,
        }


class ErocastPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?erocast\.me/playlist/(?P<playlist_id>[0-9]+)/(?P<playlist_title>[0-9a-zA-Z_-]+)'
    _TESTS = [{
        'url': 'https://erocast.me/playlist/2278/rough-hot-and-dirty',
        'info_dict': {
            'id': '2278',
            'title': 'rough-hot-and-dirty',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'https://erocast.me/playlist/1841/dilf',
        'info_dict': {
            'id': '1841',
            'title': 'dilf',
        },
        'playlist_mincount': 7,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('playlist_id')
        title = mobj.group('playlist_title')

        webpage = self._download_webpage(url, playlist_id)

        # Get URL for each track in the playlist
        entries = [self.url_result(
            'https://erocast.me/track/' + mobj.group('song_id') + '/' + mobj.group('track_url'),
            ie=ErocastIE.ie_key(), video_id=mobj.group('song_id'))
            for mobj in re.finditer(
                r'<script\b[^>]*>var\s+song_data_(?P<song_id>[0-9]+)\s*=\s*.+?\\/track\\/[0-9]+\\/(?P<track_url>.+)\"\,\"stream_url.+?</script>', webpage)]

        return self.playlist_result(entries, playlist_id, title)

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class KhinsiderBaseIE(InfoExtractor):
    def _extract_track_info(self, webpage):
        track_title = self._search_regex(r'Song name: <b>(?P<song_name>.+)</b>', webpage, 'track_title', group='song_name')
        album_title = self._search_regex(r'Album name: <b>(?P<album_name>.+)</b>', webpage, 'album_title', group='album_name')
        track_url = self._search_regex(r'href=\"(?P<link>[a-zA-z\-%0-9/\.\\:]+.mp3)\"', webpage, 'url', group='link')

        return(track_title, album_title, track_url)


class KhinsiderTrackIE(KhinsiderBaseIE):
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<album_name>[a-zA-Z0-9\-]+)/(?P<track_name>.+)\.mp3'
    _TEST = {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/fighter-s-history-arcade-gamerip/033%20%5bVoice%5d.mp3',
        'info_dict': {
            'id': '[Voice]',
            'ext': 'mp3',
            'title': '[Voice]',
            'album': "Fighter's History (Arcade) (gamerip)",
        }
    }

    def _real_extract(self, url):
        track_title = self._search_regex(self._VALID_URL, url, 'track_title', group='track_name')
        album_title = self._search_regex(self._VALID_URL, url, 'album_title', group='album_name')
        webpage = self._download_webpage(url, track_title)

        track_title, album_title, track_url = self._extract_track_info(webpage)

        formats = []
        formats.append({
            'format_id': 'mp3',
            'vcodec': 'none',
            'acodec': 'mp3',
            'url': track_url,
        })
        return {
            'id': track_title + album_title,
            'url': track_url,
            'formats': formats,
            'title': track_title,
            'album': album_title
        }


class KhinsiderAlbumIE(KhinsiderBaseIE):
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<name>[a-zA-Z0-9\-]+)$'
    _TEST = {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/r-racing-evolution',
        'info_dict': {
            'id': '3901',
            'title': 'R-Racing Evolution',
        },
        'playlist-count': 17
    }

    def _real_extract(self, url):
        album_title = self._search_regex(self._VALID_URL, url, 'name', group='name')
        webpage = self._download_webpage(url, album_title)

        album_id = self._search_regex(r'src=\"/album_views\.php\?a=(?P<playlist_id>[0-9]+)\"', webpage, album_title, group='playlist_id')
        songs = re.findall(r'\"clickable-row\"><a href=\"(?P<link>[a-zA-z\-%0-9/\.]+.mp3)\">', webpage)

        entries = []
        for song in songs:
            track_title = self._search_regex(r'/game-soundtracks/album/(?P<album_name>[a-zA-Z0-9\-]+)/(?P<track_name>.+)\.mp3',
                                             'https://downloads.khinsider.com%s' % song, 'url', group='track_name')
            song_webpage = self._download_webpage('https://downloads.khinsider.com%s' % song, track_title)
            track_title, album_title, track_url = self._extract_track_info(song_webpage)

            formats = []
            formats.append({
                'format_id': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
                'url': track_url,
            })
            entries.append({
                'id': track_title + album_title,
                'url': track_url,
                'formats': formats,
                'title': track_title,
                'album': album_title
            })

        return self.playlist_result(entries, album_id, album_title)

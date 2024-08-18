# coding: utf-8
from __future__ import unicode_literals

import re


from .common import InfoExtractor
from ..utils import (
    get_element_by_id,
    unified_strdate,
    ExtractorError,
    parse_duration)


class KhinsiderIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<album>.+?)/(?P<track>.+?)\.mp3'
    _TESTS = [{
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/legend-of-zelda-the-breath-of-the-wild-sound-selection/01%2520-%2520Main%2520Theme.mp3',
        'md5': 'ca2a50c45a0bb06d56ed48de4319d674',
        'info_dict': {
            'id': 'legend-of-zelda-the-breath-of-the-wild-sound-selection_01%2520-%2520Main%2520Theme',
            'title': 'Main Theme',
            'description': 'Download Main Theme - Legend of Zelda, The - Breath of the Wild Sound Selection soundtracks to your PC in MP3 format. Free Main Theme - Legend of Zelda, The - Breath of the Wild Sound Selection soundtracks, Main Theme - Legend of Zelda, The - Breath of the Wild Sound Selection MP3 downloads. Browse our great selection of Main Theme music. Unlimited free downloads of your favourite Legend of Zelda, The - Breath of the Wild Sound Selection albums.',
            'ext': 'mp3',
            'album': 'Legend of Zelda, The - Breath of the Wild Sound Selection',
            'track': 'Main Theme'
        }
    }, {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/doraemon-nobita-no-shin-makai-daibouken-ds-nintendo-ds/30.mp3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._search_regex(
            self._VALID_URL, url,
            'album', group='album') + '_' + self._search_regex(self._VALID_URL, url, 'track', group='track')
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'Song name: <b>(.+?)</b>', webpage, 'title', default=video_id)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage),
            'url': url,
            'ext': 'mp3',
            'album': self._html_search_regex(r'Album name: <b>(.+?)</b>', webpage, 'album name', fatal=False),
            'track': title
        }


class KhinsiderAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<id>[\w,\-,0-9]+)'
    _TESTS = [{
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/legend-of-zelda-the-breath-of-the-wild-sound-selection',
        'info_dict': {
            'id': 'legend-of-zelda-the-breath-of-the-wild-sound-selection',
            'title': 'Legend of Zelda, The - Breath of the Wild Sound Selection MP3 - Download Legend of Zelda, The - Breath of the Wild Sound Selection Soundtracks for FREE!',
            'description': 'Download Legend of Zelda, The - Breath of the Wild Sound Selection soundtracks to your PC in MP3 format. Free Legend of Zelda, The - Breath of the Wild Sound Selection soundtracks, Legend of Zelda, The - Breath of the Wild Sound Selection MP3 downloads. Browse our great selection of Legend of Zelda, The - Breath of the Wild Sound Selection music. Unlimitted free downloads of your favourite Legend of Zelda, The - Breath of the Wild Sound Selection albums.',
        },
        'playlist_mincount': 10
    }, {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/assassin-s-creed-3-the-tyranny-of-king-washington',
        'info_dict': {
            'id': 'assassin-s-creed-3-the-tyranny-of-king-washington',
            'title': 'Assassin\'s Creed III: The Tyranny of King Washington DlC OST MP3 - Download Assassin\'s Creed III: The Tyranny of King Washington DlC OST Soundtracks for FREE!',
            'description': 'Download Assassin\'s Creed III: The Tyranny of King Washington DlC OST soundtracks to your PC in MP3 format. Free Assassin\'s Creed III: The Tyranny of King Washington DlC OST soundtracks, Assassin\'s Creed III: The Tyranny of King Washington DlC OST MP3 downloads. Browse our great selection of Assassin\'s Creed III: The Tyranny of King Washington DlC OST music. Unlimitted free downloads of your favourite Assassin\'s Creed III: The Tyranny of King Washington DlC OST albums.',
        },
        'playlist_mincount': 20
    }]

    def _parse_playlist_entries(self, content, tb=None, ud=None):
        r = re.compile(r'<td class=\"clickable-row\"><a href=\"(?P<track_url>.+?)\">(?P<track_title>.+?)</a></td>[^\S]+<td class=\"clickable-row\"[^>]+?><a href=\"(.+?)\"[^>]+?>(?P<duration>[0-9,:]+)</a></td>')
        songs_info = [m.groupdict() for m in r.finditer(content)]

        if len(songs_info) <= 0:
            raise ExtractorError('No tracks found for this album.')

        entries = []
        for song_info in songs_info:
            entries.append({
                '_type': 'url_transparent',
                'ie_key': KhinsiderIE.ie_key(),
                'title': song_info.get('track_title'),
                'url': 'https://downloads.khinsider.com' + song_info.get('track_url'),
                'duration': parse_duration(song_info.get('duration')),
                'thumbnail': tb,
                'upload_date': unified_strdate(ud)
            })

        return entries

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.+?)[^\S]+?</title>', webpage, 'title', default=video_id)
        upload_date = self._html_search_regex(r'Date added: <b>(.+?)</b>', webpage, 'upload date', fatal=False)
        tb = self._html_search_regex(
            r'<a href=\"(https://vgmsite.com/(.+?).jpg)\" target=\"_blank\">',
            webpage, 'thumbnail', fatal=False) or self._html_search_regex(
            r'<img src=\"(https://vgmsite.com/soundtracks/(.+?).jpg)\" border=\"0\">',
            webpage, 'thumbnail', fatal=False)

        songlist = get_element_by_id('songlist', webpage)
        entries = self._parse_playlist_entries(songlist, tb=tb, ud=upload_date)

        return self.playlist_result(
            entries,
            playlist_id=video_id,
            playlist_title=title,
            playlist_description=self._html_search_meta('description', webpage))

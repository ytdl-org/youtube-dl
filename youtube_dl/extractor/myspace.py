from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
)


class MySpaceIE(InfoExtractor):
    _VALID_URL = r'https?://myspace\.com/([^/]+)/(?P<mediatype>video/[^/]+/|music/song/.*?)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'https://myspace.com/coldplay/video/viva-la-vida/100008689',
            'info_dict': {
                'id': '100008689',
                'ext': 'flv',
                'title': 'Viva La Vida',
                'description': 'The official Viva La Vida video, directed by Hype Williams',
                'uploader': 'Coldplay',
                'uploader_id': 'coldplay',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        # song
        {
            'url': 'https://myspace.com/spiderbags/music/song/darkness-in-my-heart-39008454-27041242',
            'info_dict': {
                'id': '39008454',
                'ext': 'flv',
                'title': 'Darkness In My Heart',
                'uploader_id': 'spiderbags',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        player_url = self._search_regex(
            r'playerSwf":"([^"?]*)', webpage, 'player URL')

        if mobj.group('mediatype').startswith('music/song'):
            # songs don't store any useful info in the 'context' variable
            song_data = self._search_regex(
                r'''<button.*data-song-id=(["\'])%s\1.*''' % video_id,
                webpage, 'song_data', default=None, group=0)
            if song_data is None:
                self.to_screen(
                    '%s: No downloadable song on this page' % video_id)
                return
            def search_data(name):
                return self._search_regex(
                    r'''data-%s=([\'"])(.*?)\1''' % name,
                    song_data, name, default='', group=2)
            streamUrl = search_data('stream-url')
            info = {
                'id': video_id,
                'title': self._og_search_title(webpage),
                'uploader': search_data('artist-name'),
                'uploader_id': search_data('artist-username'),
                'playlist': search_data('album-title'),
                'thumbnail': self._og_search_thumbnail(webpage),
            }
        else:
            context = json.loads(self._search_regex(
                r'context = ({.*?});', webpage, 'context'))
            video = context['video']
            streamUrl = video['streamUrl']
            info = {
                'id': compat_str(video['mediaId']),
                'title': video['title'],
                'description': video['description'],
                'thumbnail': video['imageUrl'],
                'uploader': video['artistName'],
                'uploader_id': video['artistUsername'],
            }

        rtmp_url, play_path = streamUrl.split(';', 1)
        info.update({
            'url': rtmp_url,
            'play_path': play_path,
            'player_url': player_url,
            'ext': 'flv',
        })
        return info

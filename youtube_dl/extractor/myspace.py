# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import ExtractorError


class MySpaceIE(InfoExtractor):
    _VALID_URL = r'https?://myspace\.com/([^/]+)/(?P<mediatype>video/[^/]+/|music/song/.*?)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'https://myspace.com/fiveminutestothestage/video/little-big-town/109594919',
            'info_dict': {
                'id': '109594919',
                'ext': 'flv',
                'title': 'Little Big Town',
                'description': 'This country quartet was all smiles while playing a sold out show at the Pacific Amphitheatre in Orange County, California.',
                'uploader': 'Five Minutes to the Stage',
                'uploader_id': 'fiveminutestothestage',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        # songs
        {
            'url': 'https://myspace.com/killsorrow/music/song/of-weakened-soul...-93388656-103880681',
            'info_dict': {
                'id': '93388656',
                'ext': 'flv',
                'title': 'Of weakened soul...',
                'uploader': 'Killsorrow',
                'uploader_id': 'killsorrow',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        }, {
            'add_ie': ['Vevo'],
            'url': 'https://myspace.com/threedaysgrace/music/song/animal-i-have-become-28400208-28218041',
            'info_dict': {
                'id': 'USZM20600099',
                'ext': 'mp4',
                'title': 'Animal I Have Become',
                'uploader': 'Three Days Grace',
                'timestamp': int,
                'upload_date': '20060502',
            },
            'skip': 'VEVO is only available in some countries',
        }, {
            'add_ie': ['Youtube'],
            'url': 'https://myspace.com/starset2/music/song/first-light-95799905-106964426',
            'info_dict': {
                'id': 'ypWvQgnJrSU',
                'ext': 'mp4',
                'title': 'Starset - First Light',
                'description': 'md5:2d5db6c9d11d527683bcda818d332414',
                'uploader': 'Jacob Soren',
                'uploader_id': 'SorenPromotions',
                'upload_date': '20140725',
            }
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
                # some songs in an album are not playable
                self.report_warning(
                    '%s: No downloadable song on this page' % video_id)
                return

            def search_data(name):
                return self._search_regex(
                    r'''data-%s=([\'"])(?P<data>.*?)\1''' % name,
                    song_data, name, default='', group='data')
            streamUrl = search_data('stream-url')
            if not streamUrl:
                vevo_id = search_data('vevo-id')
                youtube_id = search_data('youtube-id')
                if vevo_id:
                    self.to_screen('Vevo video detected: %s' % vevo_id)
                    return self.url_result('vevo:%s' % vevo_id, ie='Vevo')
                elif youtube_id:
                    self.to_screen('Youtube video detected: %s' % youtube_id)
                    return self.url_result(youtube_id, ie='Youtube')
                else:
                    raise ExtractorError(
                        'Found song but don\'t know how to download it')
            info = {
                'id': video_id,
                'title': self._og_search_title(webpage),
                'uploader': search_data('artist-name'),
                'uploader_id': search_data('artist-username'),
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


class MySpaceAlbumIE(InfoExtractor):
    IE_NAME = 'MySpace:album'
    _VALID_URL = r'https?://myspace\.com/([^/]+)/music/album/(?P<title>.*-)(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://myspace.com/starset2/music/album/transmissions-19455773',
        'info_dict': {
            'title': 'Transmissions',
            'id': '19455773',
        },
        'playlist_count': 14,
        'skip': 'this album is only available in some countries',
    }, {
        'url': 'https://myspace.com/killsorrow/music/album/the-demo-18596029',
        'info_dict': {
            'title': 'The Demo',
            'id': '18596029',
        },
        'playlist_count': 5,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        display_id = mobj.group('title') + playlist_id
        webpage = self._download_webpage(url, display_id)
        tracks_paths = re.findall(r'"music:song" content="(.*?)"', webpage)
        if not tracks_paths:
            raise ExtractorError(
                '%s: No songs found, try using proxy' % display_id,
                expected=True)
        entries = [
            self.url_result(t_path, ie=MySpaceIE.ie_key())
            for t_path in tracks_paths]
        return {
            '_type': 'playlist',
            'id': playlist_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage),
            'entries': entries,
        }

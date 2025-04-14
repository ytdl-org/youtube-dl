# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
)


class MySpaceIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        myspace\.com/[^/]+/
                        (?P<mediatype>
                            video/[^/]+/(?P<video_id>\d+)|
                            music/song/[^/?#&]+-(?P<song_id>\d+)-\d+(?:[/?#&]|$)
                        )
                    '''

    _TESTS = [{
        'url': 'https://myspace.com/fiveminutestothestage/video/little-big-town/109594919',
        'md5': '9c1483c106f4a695c47d2911feed50a7',
        'info_dict': {
            'id': '109594919',
            'ext': 'mp4',
            'title': 'Little Big Town',
            'description': 'This country quartet was all smiles while playing a sold out show at the Pacific Amphitheatre in Orange County, California.',
            'uploader': 'Five Minutes to the Stage',
            'uploader_id': 'fiveminutestothestage',
            'timestamp': 1414108751,
            'upload_date': '20141023',
        },
    }, {
        # songs
        'url': 'https://myspace.com/killsorrow/music/song/of-weakened-soul...-93388656-103880681',
        'md5': '1d7ee4604a3da226dd69a123f748b262',
        'info_dict': {
            'id': '93388656',
            'ext': 'm4a',
            'title': 'Of weakened soul...',
            'uploader': 'Killsorrow',
            'uploader_id': 'killsorrow',
        },
    }, {
        'add_ie': ['Youtube'],
        'url': 'https://myspace.com/threedaysgrace/music/song/animal-i-have-become-28400208-28218041',
        'info_dict': {
            'id': 'xqds0B_meys',
            'ext': 'webm',
            'title': 'Three Days Grace - Animal I Have Become',
            'description': 'md5:8bd86b3693e72a077cf863a8530c54bb',
            'uploader': 'ThreeDaysGraceVEVO',
            'uploader_id': 'ThreeDaysGraceVEVO',
            'upload_date': '20091002',
        },
    }, {
        'url': 'https://myspace.com/starset2/music/song/first-light-95799905-106964426',
        'only_matching': True,
    }, {
        'url': 'https://myspace.com/thelargemouthbassband/music/song/02-pure-eyes.mp3-94422330-105113388',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id') or mobj.group('song_id')
        is_song = mobj.group('mediatype').startswith('music/song')
        webpage = self._download_webpage(url, video_id)
        player_url = self._search_regex(
            r'videoSwf":"([^"?]*)', webpage, 'player URL', fatal=False)

        def formats_from_stream_urls(stream_url, hls_stream_url, http_stream_url, width=None, height=None):
            formats = []
            vcodec = 'none' if is_song else None
            if hls_stream_url:
                formats.append({
                    'format_id': 'hls',
                    'url': hls_stream_url,
                    'protocol': 'm3u8_native',
                    'ext': 'm4a' if is_song else 'mp4',
                    'vcodec': vcodec,
                })
            if stream_url and player_url:
                rtmp_url, play_path = stream_url.split(';', 1)
                formats.append({
                    'format_id': 'rtmp',
                    'url': rtmp_url,
                    'play_path': play_path,
                    'player_url': player_url,
                    'protocol': 'rtmp',
                    'ext': 'flv',
                    'width': width,
                    'height': height,
                    'vcodec': vcodec,
                })
            if http_stream_url:
                formats.append({
                    'format_id': 'http',
                    'url': http_stream_url,
                    'width': width,
                    'height': height,
                    'vcodec': vcodec,
                })
            return formats

        if is_song:
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
            formats = formats_from_stream_urls(
                search_data('stream-url'), search_data('hls-stream-url'),
                search_data('http-stream-url'))
            if not formats:
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
            self._sort_formats(formats)
            return {
                'id': video_id,
                'title': self._og_search_title(webpage),
                'uploader': search_data('artist-name'),
                'uploader_id': search_data('artist-username'),
                'thumbnail': self._og_search_thumbnail(webpage),
                'duration': int_or_none(search_data('duration')),
                'formats': formats,
            }
        else:
            video = self._parse_json(self._search_regex(
                r'context = ({.*?});', webpage, 'context'),
                video_id)['video']
            formats = formats_from_stream_urls(
                video.get('streamUrl'), video.get('hlsStreamUrl'),
                video.get('mp4StreamUrl'), int_or_none(video.get('width')),
                int_or_none(video.get('height')))
            self._sort_formats(formats)
            return {
                'id': video_id,
                'title': video['title'],
                'description': video.get('description'),
                'thumbnail': video.get('imageUrl'),
                'uploader': video.get('artistName'),
                'uploader_id': video.get('artistUsername'),
                'duration': int_or_none(video.get('duration')),
                'timestamp': parse_iso8601(video.get('dateAdded')),
                'formats': formats,
            }


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
        return self.playlist_result(entries, playlist_id, self._og_search_title(webpage))


class MySpaceArtistIE(InfoExtractor):
    IE_NAME = 'MySpace:artist'
    _VALID_URL = r'https?://myspace\.com/(?P<artist>[^/]*)/music/songs'

    _TEST = {
        'url': 'https://myspace.com/studio99/music/songs/',
        'info_dict': {
            'title': 'Studio 99 IS CLOSED!! R.I.P.',
        },
        'playlist_count': 4,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('artist')
        webpage = self._download_webpage(url, display_id)
        tracks_paths = re.findall(r'<meta itemprop="url" content ="(.*?)">', webpage)
        if not tracks_paths:
            raise ExtractorError(
                '%s: No songs found, try using proxy' % display_id,
                expected=True)

        entries = [
            self.url_result('https://myspace.com/' + display_id + t_path, ie=MySpaceIE.ie_key())
            for t_path in tracks_paths if t_path.startswith('/music/song/')]
        #   if we invert this if, we get album urls. but not all music are in alba.
        #   Also the musics in alba are already here individually

        return self.playlist_result(entries, playlist_title=self._og_search_title(webpage))

# coding: utf-8
from __future__ import unicode_literals

import re
import hashlib

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
)


class YandexMusicBaseIE(InfoExtractor):
    @staticmethod
    def _handle_error(response):
        if isinstance(response, dict):
            error = response.get('error')
            if error:
                raise ExtractorError(error, expected=True)
            if response.get('type') == 'captcha' or 'captcha' in response:
                YandexMusicBaseIE._raise_captcha()

    @staticmethod
    def _raise_captcha():
        raise ExtractorError(
            'YandexMusic has considered youtube-dl requests automated and '
            'asks you to solve a CAPTCHA. You can either wait for some '
            'time until unblocked and optionally use --sleep-interval '
            'in future or alternatively you can go to https://music.yandex.ru/ '
            'solve CAPTCHA, then export cookies and pass cookie file to '
            'youtube-dl with --cookies',
            expected=True)

    def _download_webpage(self, *args, **kwargs):
        webpage = super(YandexMusicBaseIE, self)._download_webpage(*args, **kwargs)
        if 'Нам очень жаль, но&nbsp;запросы, поступившие с&nbsp;вашего IP-адреса, похожи на&nbsp;автоматические.' in webpage:
            self._raise_captcha()
        return webpage

    def _download_json(self, *args, **kwargs):
        response = super(YandexMusicBaseIE, self)._download_json(*args, **kwargs)
        self._handle_error(response)
        return response


class YandexMusicTrackIE(YandexMusicBaseIE):
    IE_NAME = 'yandexmusic:track'
    IE_DESC = 'Яндекс.Музыка - Трек'
    _VALID_URL = r'https?://music\.yandex\.(?:ru|kz|ua|by)/album/(?P<album_id>\d+)/track/(?P<id>\d+)'

    _TEST = {
        'url': 'http://music.yandex.ru/album/540508/track/4878838',
        'md5': 'f496818aa2f60b6c0062980d2e00dc20',
        'info_dict': {
            'id': '4878838',
            'ext': 'mp3',
            'title': 'Carlo Ambrosio & Fabio Di Bari, Carlo Ambrosio - Gypsy Eyes 1',
            'filesize': 4628061,
            'duration': 193.04,
            'track': 'Gypsy Eyes 1',
            'album': 'Gypsy Soul',
            'album_artist': 'Carlo Ambrosio',
            'artist': 'Carlo Ambrosio & Fabio Di Bari, Carlo Ambrosio',
            'release_year': '2009',
        },
        'skip': 'Travis CI servers blocked by YandexMusic',
    }

    def _get_track_url(self, storage_dir, track_id):
        data = self._download_json(
            'http://music.yandex.ru/api/v1.5/handlers/api-jsonp.jsx?action=getTrackSrc&p=download-info/%s'
            % storage_dir,
            track_id, 'Downloading track location JSON')

        # Each string is now wrapped in a list, this is probably only temporarily thus
        # supporting both scenarios (see https://github.com/rg3/youtube-dl/issues/10193)
        for k, v in data.items():
            if v and isinstance(v, list):
                data[k] = v[0]

        key = hashlib.md5(('XGRlBW9FXlekgbPrRHuSiA' + data['path'][1:] + data['s']).encode('utf-8')).hexdigest()
        storage = storage_dir.split('.')

        return ('http://%s/get-mp3/%s/%s?track-id=%s&from=service-10-track&similarities-experiment=default'
                % (data['host'], key, data['ts'] + data['path'], storage[1]))

    def _get_track_info(self, track):
        thumbnail = None
        cover_uri = track.get('albums', [{}])[0].get('coverUri')
        if cover_uri:
            thumbnail = cover_uri.replace('%%', 'orig')
            if not thumbnail.startswith('http'):
                thumbnail = 'http://' + thumbnail

        track_title = track['title']
        track_info = {
            'id': track['id'],
            'ext': 'mp3',
            'url': self._get_track_url(track['storageDir'], track['id']),
            'filesize': int_or_none(track.get('fileSize')),
            'duration': float_or_none(track.get('durationMs'), 1000),
            'thumbnail': thumbnail,
            'track': track_title,
        }

        def extract_artist(artist_list):
            if artist_list and isinstance(artist_list, list):
                artists_names = [a['name'] for a in artist_list if a.get('name')]
                if artists_names:
                    return ', '.join(artists_names)

        albums = track.get('albums')
        if albums and isinstance(albums, list):
            album = albums[0]
            if isinstance(album, dict):
                year = album.get('year')
                track_info.update({
                    'album': album.get('title'),
                    'album_artist': extract_artist(album.get('artists')),
                    'release_year': compat_str(year) if year else None,
                })

        track_artist = extract_artist(track.get('artists'))
        if track_artist:
            track_info.update({
                'artist': track_artist,
                'title': '%s - %s' % (track_artist, track_title),
            })
        else:
            track_info['title'] = track_title
        return track_info

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        album_id, track_id = mobj.group('album_id'), mobj.group('id')

        track = self._download_json(
            'http://music.yandex.ru/handlers/track.jsx?track=%s:%s' % (track_id, album_id),
            track_id, 'Downloading track JSON')['track']

        return self._get_track_info(track)


class YandexMusicPlaylistBaseIE(YandexMusicBaseIE):
    def _build_playlist(self, tracks):
        return [
            self.url_result(
                'http://music.yandex.ru/album/%s/track/%s' % (track['albums'][0]['id'], track['id']))
            for track in tracks if track.get('albums') and isinstance(track.get('albums'), list)]


class YandexMusicAlbumIE(YandexMusicPlaylistBaseIE):
    IE_NAME = 'yandexmusic:album'
    IE_DESC = 'Яндекс.Музыка - Альбом'
    _VALID_URL = r'https?://music\.yandex\.(?:ru|kz|ua|by)/album/(?P<id>\d+)/?(\?|$)'

    _TEST = {
        'url': 'http://music.yandex.ru/album/540508',
        'info_dict': {
            'id': '540508',
            'title': 'Carlo Ambrosio - Gypsy Soul (2009)',
        },
        'playlist_count': 50,
        'skip': 'Travis CI servers blocked by YandexMusic',
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        album = self._download_json(
            'http://music.yandex.ru/handlers/album.jsx?album=%s' % album_id,
            album_id, 'Downloading album JSON')

        entries = self._build_playlist(album['volumes'][0])

        title = '%s - %s' % (album['artists'][0]['name'], album['title'])
        year = album.get('year')
        if year:
            title += ' (%s)' % year

        return self.playlist_result(entries, compat_str(album['id']), title)


class YandexMusicPlaylistIE(YandexMusicPlaylistBaseIE):
    IE_NAME = 'yandexmusic:playlist'
    IE_DESC = 'Яндекс.Музыка - Плейлист'
    _VALID_URL = r'https?://music\.yandex\.(?P<tld>ru|kz|ua|by)/users/(?P<user>[^/]+)/playlists/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://music.yandex.ru/users/music.partners/playlists/1245',
        'info_dict': {
            'id': '1245',
            'title': 'Что слушают Enter Shikari',
            'description': 'md5:3b9f27b0efbe53f2ee1e844d07155cc9',
        },
        'playlist_count': 6,
        'skip': 'Travis CI servers blocked by YandexMusic',
    }, {
        # playlist exceeding the limit of 150 tracks shipped with webpage (see
        # https://github.com/rg3/youtube-dl/issues/6666)
        'url': 'https://music.yandex.ru/users/ya.playlist/playlists/1036',
        'info_dict': {
            'id': '1036',
            'title': 'Музыка 90-х',
        },
        'playlist_mincount': 300,
        'skip': 'Travis CI servers blocked by YandexMusic',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        tld = mobj.group('tld')
        user = mobj.group('user')
        playlist_id = mobj.group('id')

        playlist = self._download_json(
            'https://music.yandex.%s/handlers/playlist.jsx' % tld,
            playlist_id, 'Downloading missing tracks JSON',
            fatal=False,
            headers={
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest',
                'X-Retpath-Y': url,
            },
            query={
                'owner': user,
                'kinds': playlist_id,
                'light': 'true',
                'lang': tld,
                'external-domain': 'music.yandex.%s' % tld,
                'overembed': 'false',
            })['playlist']

        tracks, track_ids = playlist['tracks'], map(compat_str, playlist['trackIds'])

        # tracks dictionary shipped with playlist.jsx API is limited to 150 tracks,
        # missing tracks should be retrieved manually.
        if len(tracks) < len(track_ids):
            present_track_ids = set([
                compat_str(track['id'])
                for track in tracks if track.get('id')])
            missing_track_ids = [
                track_id for track_id in track_ids
                if track_id not in present_track_ids]
            missing_tracks = self._download_json(
                'https://music.yandex.%s/handlers/track-entries.jsx' % tld,
                playlist_id, 'Downloading missing tracks JSON',
                fatal=False,
                headers={
                    'Referer': url,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                query={
                    'entries': ','.join(missing_track_ids),
                    'lang': tld,
                    'external-domain': 'music.yandex.%s' % tld,
                    'overembed': 'false',
                    'strict': 'true',
                })
            if missing_tracks:
                tracks.extend(missing_tracks)

        return self.playlist_result(
            self._build_playlist(tracks),
            compat_str(playlist_id),
            playlist.get('title'), playlist.get('description'))

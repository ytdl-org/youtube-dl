# coding=utf-8
from __future__ import unicode_literals

import re
import hashlib

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    float_or_none,
)


class YandexMusicBaseIE(InfoExtractor):
    def _get_track_url(self, storage_dir, track_id):
        data = self._download_json(
            'http://music.yandex.ru/api/v1.5/handlers/api-jsonp.jsx?action=getTrackSrc&p=download-info/%s'
            % storage_dir,
            track_id, 'Downloading track location JSON')

        key = hashlib.md5(('XGRlBW9FXlekgbPrRHuSiA' + data['path'][1:] + data['s']).encode('utf-8')).hexdigest()
        storage = storage_dir.split('.')

        return ('http://%s/get-mp3/%s/%s?track-id=%s&from=service-10-track&similarities-experiment=default'
                % (data['host'], key, data['ts'] + data['path'], storage[1]))

    def _get_track_info(self, track):
        return {
            'id': track['id'],
            'ext': 'mp3',
            'url': self._get_track_url(track['storageDir'], track['id']),
            'title': '%s - %s' % (track['artists'][0]['name'], track['title']),
            'filesize': int_or_none(track.get('fileSize')),
            'duration': float_or_none(track.get('durationMs'), 1000),
        }


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
            'title': 'Carlo Ambrosio - Gypsy Eyes 1',
            'filesize': 4628061,
            'duration': 193.04,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        album_id, track_id = mobj.group('album_id'), mobj.group('id')

        track = self._download_json(
            'http://music.yandex.ru/handlers/track.jsx?track=%s:%s' % (track_id, album_id),
            track_id, 'Downloading track JSON')['track']

        return self._get_track_info(track)


class YandexMusicAlbumIE(YandexMusicBaseIE):
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
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        album = self._download_json(
            'http://music.yandex.ru/handlers/album.jsx?album=%s' % album_id,
            album_id, 'Downloading album JSON')

        entries = [self._get_track_info(track) for track in album['volumes'][0]]

        title = '%s - %s' % (album['artists'][0]['name'], album['title'])
        year = album.get('year')
        if year:
            title += ' (%s)' % year

        return self.playlist_result(entries, compat_str(album['id']), title)


class YandexMusicPlaylistIE(YandexMusicBaseIE):
    IE_NAME = 'yandexmusic:playlist'
    IE_DESC = 'Яндекс.Музыка - Плейлист'
    _VALID_URL = r'https?://music\.yandex\.(?:ru|kz|ua|by)/users/[^/]+/playlists/(?P<id>\d+)'

    _TEST = {
        'url': 'http://music.yandex.ru/users/music.partners/playlists/1245',
        'info_dict': {
            'id': '1245',
            'title': 'Что слушают Enter Shikari',
            'description': 'md5:3b9f27b0efbe53f2ee1e844d07155cc9',
        },
        'playlist_count': 6,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        playlist = self._parse_json(
            self._search_regex(
                r'var\s+Mu\s*=\s*({.+?});\s*</script>', webpage, 'player'),
            playlist_id)['pageData']['playlist']

        entries = [self._get_track_info(track) for track in playlist['tracks']]

        return self.playlist_result(
            entries, compat_str(playlist_id),
            playlist['title'], playlist.get('description'))

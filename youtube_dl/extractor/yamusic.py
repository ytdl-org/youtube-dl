# coding=utf-8
from __future__ import unicode_literals

import re
import hashlib
import time

from .common import InfoExtractor

class YandexMusicAlbumIE(InfoExtractor):
    _VALID_URL = r'http://music.yandex.ru/album/(?P<id>\d+)'

    def _get_track_url(self, storage_dir, track_id):
        data = self._download_json('http://music.yandex.ru/api/v1.5/handlers/api-jsonp.jsx?requestId=2&nc=%d&action=getTrackSrc&p=download-info/%s/2.mp3' % (time.time(), storage_dir), track_id)

        hsh = hashlib.md5()
        hsh.update('XGRlBW9FXlekgbPrRHuSiA' + data['path'][1:] + data['s'])
        hash = hsh.hexdigest()
        storage = storage_dir.split('.')

        return 'http://%s/get-mp3/%s/%s?track-id=%s&from=service-10-track&similarities-experiment=default' % (data['host'], hash, data['ts'] + data['path'], storage[1])

    def _get_album_id_and_data(self, url):
        matched = re.match(self._VALID_URL, url)
        id = matched.group('id')

        webpage = self._download_webpage(url, id)
        data = self._parse_json(
            self._search_regex(
                r'var\s+Mu\s+=\s+(.+?);\s+<\/script>', webpage, 'player'),
            id)
        return id, data['pageData']

    def _real_extract(self, url):

        id, data = self._get_album_id_and_data(url)

        entries = []

        for track in data['volumes'][0]:
            entries.append({
                'id': track['id'],
                'ext': 'mp3',
                'url': self._get_track_url(track['storageDir'], track['id']),
                'title': track['artists'][0]['name'] + ' - ' + track['title'],
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': id,
            'title': data['title'],
        }

class YandexMusicPlaylistIE(YandexMusicAlbumIE):
    _VALID_URL = r'http://music.yandex.ru/users/(?P<user_name>[^/]+)/playlists/(?P<id>\d+)'

    def _real_extract(self, url):
        id, data = self._get_album_id_and_data(url)
        data = data['playlist']

        entries = []

        for track in data['tracks']:
            entries.append({
                'id': track['id'],
                'ext': 'mp3',
                'url': self._get_track_url(track['storageDir'], track['id']),
                'title': track['artists'][0]['name'] + ' - ' + track['title'],
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': id,
            'title': data['title'],
        }

class YandexMusicTrackIE(YandexMusicAlbumIE):
    _VALID_URL = r'http://music.yandex.ru/album/(?P<album_id>\d+)/track/(?P<id>\d+)'
    _TEST = {
        'url': 'http://music.yandex.ru/album/540508/track/4878838',
        'info_dict': {
            'id': '4878838',
            'ext': 'mp3',
            'title': 'Carlo Ambrosio - Gypsy Eyes 1',
        }
    }

    def _real_extract(self, url):

        id, data = self._get_album_id_and_data(url)

        for track in data['volumes'][0]:
            if track['id'] == id:
                track_url = self._get_track_url(track['storageDir'], id)
                break

        return {
            'id': id,
            'ext': 'mp3',
            'url': track_url,
            'title': track['artists'][0]['name'] + ' - ' + track['title'],
        }

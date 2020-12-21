# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none, unified_timestamp


class StreetVoiceIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?streetvoice\.com/[^/]+/songs/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://streetvoice.com/lekimberleyy/songs/630281/',
        'md5': '515d4bfdfe337039d9efaa53be24484d',
        'info_dict': {
            'id': '630281',
            'ext': 'mp3',
            'title': '郵票Good Times feat. 瘦子E.SO',
            'description': 'Kimberley - 郵票Good Times feat. 瘦子E.SO',
            'thumbnail': r're:^https?://.*\.jpg',
            'uploader': 'lekimberleyy',
            'uploader_id': '2674557',
            'duration': 236,
            'upload_date': '20201216',
            'timestamp': 1608110177
        }
    }, {
        'url': 'https://tw.streetvoice.com/ConstantanChange/songs/628471/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        song_id = self._match_id(url)

        song = self._download_json(
            'https://streetvoice.com/api/v4/song/%s/' % song_id, song_id, note="Downloading song details")

        song_file = self._download_json(
            'https://streetvoice.com/api/v4/song/%s/hls/file/' % song_id, song_id, data=b'', note="Downloading song data")

        title = song['name']
        formats = [{'url': song_file['file'], 'format_id': 'hls', 'protocol': 'm3u8', 'ext': 'mp3'}]

        author = uploader = uploader_id = album_name = album_type = None
        user_data = song.get('user')

        if (user_data is not None):
            user_profile = user_data.get('profile')
            if (user_profile is not None):
                author = user_profile.get('nickname')
            uploader = user_data.get('username')
            uploader_id = compat_str(user_data.get('id'))

        album_data = song.get('album')
        if (album_data is not None):
            album_name = album_data.get('name')
            album_type = album_data.get('type')


        return {
            'id': song_id,
            'title': title,
            'description': '%s - %s' % (author, title),
            'thumbnail': self._proto_relative_url(song.get('image'), 'http:'),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
            'duration': int_or_none(song.get('length')),
            'view_count': int_or_none(song.get('plays_count')),
            'like_count': int_or_none(song.get('like_count')),
            'comment_count': int_or_none(song.get('comments_count')),
            'timestamp': unified_timestamp(song.get('publish_at')),
            'repost_count': int_or_none(song.get('share_count')),
            'album': album_name,
            'album_type': album_type
        }

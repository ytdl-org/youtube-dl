# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_element,
    xpath_text,
    xpath_with_ns,
    int_or_none,
    ExtractorError
)
from ..compat import compat_urllib_parse_unquote


class XiamiBaseIE(InfoExtractor):

    _XML_BASE_URL = 'http://www.xiami.com/song/playlist/id'
    _NS_MAP = {'xm': 'http://xspf.org/ns/0/'}

    def _extract_track(self, track):
        artist = xpath_text(track, xpath_with_ns('xm:artist', self._NS_MAP), default='')
        artist = artist.split(';')

        ret = {
            'id': xpath_text(track, xpath_with_ns('xm:song_id', self._NS_MAP)),
            'title': xpath_text(track, xpath_with_ns('xm:title', self._NS_MAP)),
            'album': xpath_text(track, xpath_with_ns('xm:album_name', self._NS_MAP)),
            'artist': ';'.join(artist) if artist else None,
            'creator': artist[0] if artist else None,
            'url': self._decrypt(xpath_text(track, xpath_with_ns('xm:location', self._NS_MAP))),
            'thumbnail': xpath_text(track, xpath_with_ns('xm:pic', self._NS_MAP), default=None),
            'duration': int_or_none(xpath_text(track, xpath_with_ns('xm:length', self._NS_MAP))),
        }

        lyrics_url = xpath_text(track, xpath_with_ns('xm:lyric', self._NS_MAP))
        if lyrics_url and lyrics_url.endswith('.lrc'):
            ret['description'] = self._download_webpage(lyrics_url, ret['id'])
        return ret

    def _extract_xml(self, _id, typ=''):
        playlist = self._download_xml('%s/%s%s' % (self._XML_BASE_URL, _id, typ), _id)
        tracklist = xpath_element(playlist, xpath_with_ns('./xm:trackList', self._NS_MAP))

        if not len(tracklist):
            raise ExtractorError('No track found')
        return [self._extract_track(track) for track in tracklist]

    @staticmethod
    def _decrypt(origin):
        n = int(origin[0])
        origin = origin[1:]
        short_lenth = len(origin) // n
        long_num = len(origin) - short_lenth * n
        l = tuple()
        for i in range(0, n):
            length = short_lenth
            if i < long_num:
                length += 1
            l += (origin[0:length], )
            origin = origin[length:]
        ans = ''
        for i in range(0, short_lenth + 1):
            for j in range(0, n):
                if len(l[j])>i:
                    ans += l[j][i]
        return compat_urllib_parse_unquote(ans).replace('^', '0')


class XiamiIE(XiamiBaseIE):
    IE_NAME = 'xiami:song'
    IE_DESC = '虾米音乐'
    _VALID_URL = r'http://www\.xiami\.com/song/(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.xiami.com/song/1775610518',
            'md5': '521dd6bea40fd5c9c69f913c232cb57e',
            'info_dict': {
                'id': '1775610518',
                'ext': 'mp3',
                'title': 'Woman',
                'creator': 'HONNE',
                'album': 'Woman',
                'thumbnail': r're:http://img\.xiami\.net/images/album/.*\.jpg',
                'description': 'md5:052ec7de41ca19f67e7fd70a1bfc4e0b',
            }
        },
        {
            'url': 'http://www.xiami.com/song/1775256504',
            'md5': '932a3abd45c6aa2b1fdbe028fcb4c4fc',
            'info_dict': {
                'id': '1775256504',
                'ext': 'mp3',
                'title': '悟空',
                'creator': '戴荃',
                'album': '悟空',
                'description': 'md5:206e67e84f9bed1d473d04196a00b990',
            }
        },
    ]

    def _real_extract(self, url):
        _id = self._match_id(url)
        return self._extract_xml(_id)[0]


class XiamiAlbumIE(XiamiBaseIE):
    IE_NAME = 'xiami:album'
    IE_DESC = '虾米音乐 - 专辑'
    _VALID_URL = r'http://www\.xiami\.com/album/(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.xiami.com/album/2100300444',
            'info_dict': {
                'id': '2100300444',
            },
            'playlist_count': 10,
        },
        {
            'url': 'http://www.xiami.com/album/512288?spm=a1z1s.6843761.1110925389.6.hhE9p9',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        _id = self._match_id(url)
        return self.playlist_result(self._extract_xml(_id, '/type/1'), _id)


class XiamiArtistIE(XiamiBaseIE):
    IE_NAME = 'xiami:artist'
    IE_DESC = '虾米音乐 - 歌手'
    _VALID_URL = r'http://www\.xiami\.com/artist/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.xiami.com/artist/2132?spm=0.0.0.0.dKaScp',
        'info_dict': {
            'id': '2132',
        },
        'playlist_count': 20,
    }

    def _real_extract(self, url):
        _id = self._match_id(url)
        return self.playlist_result(self._extract_xml(_id, '/type/2'), _id)


class XiamiCollectionIE(XiamiBaseIE):
    IE_NAME = 'xiami:collection'
    IE_DESC = '虾米音乐 - 精选集'
    _VALID_URL = r'http://www\.xiami\.com/collect/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.xiami.com/collect/156527391?spm=a1z1s.2943601.6856193.12.4jpBnr',
        'info_dict': {
            'id': '156527391',
        },
        'playlist_count': 26,
    }

    def _real_extract(self, url):
        _id = self._match_id(url)
        return self.playlist_result(self._extract_xml(_id, '/type/3'), _id)

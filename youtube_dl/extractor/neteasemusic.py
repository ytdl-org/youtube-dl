# coding: utf-8
from __future__ import unicode_literals

from hashlib import md5
from base64 import b64encode
from datetime import datetime
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_str,
    compat_itertools_count,
)
from ..utils import sanitized_Request


class NetEaseMusicBaseIE(InfoExtractor):
    _FORMATS = ['bMusic', 'mMusic', 'hMusic']
    _NETEASE_SALT = '3go8&$8*3*3h0k(2)2'
    _API_BASE = 'http://music.163.com/api/'

    @classmethod
    def _encrypt(cls, dfsid):
        salt_bytes = bytearray(cls._NETEASE_SALT.encode('utf-8'))
        string_bytes = bytearray(compat_str(dfsid).encode('ascii'))
        salt_len = len(salt_bytes)
        for i in range(len(string_bytes)):
            string_bytes[i] = string_bytes[i] ^ salt_bytes[i % salt_len]
        m = md5()
        m.update(bytes(string_bytes))
        result = b64encode(m.digest()).decode('ascii')
        return result.replace('/', '_').replace('+', '-')

    @classmethod
    def extract_formats(cls, info):
        formats = []
        for song_format in cls._FORMATS:
            details = info.get(song_format)
            if not details:
                continue
            formats.append({
                'url': 'http://m5.music.126.net/%s/%s.%s' %
                       (cls._encrypt(details['dfsId']), details['dfsId'],
                        details['extension']),
                'ext': details.get('extension'),
                'abr': details.get('bitrate', 0) / 1000,
                'format_id': song_format,
                'filesize': details.get('size'),
                'asr': details.get('sr')
            })
        return formats

    @classmethod
    def convert_milliseconds(cls, ms):
        return int(round(ms / 1000.0))

    def query_api(self, endpoint, video_id, note):
        req = sanitized_Request('%s%s' % (self._API_BASE, endpoint))
        req.add_header('Referer', self._API_BASE)
        return self._download_json(req, video_id, note)


class NetEaseMusicIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:song'
    IE_DESC = '网易云音乐'
    _VALID_URL = r'https?://music\.163\.com/(#/)?song\?id=(?P<id>[0-9]+)'
    _TESTS = [{
        'note': 'origin + translated lyrics, with time tag need to be fixed',
        'url': 'http://music.163.com/#/song?id=32102397',
        'md5': 'f2e97280e6345c74ba9d5677dd5dcb45',
        'info_dict': {
            'id': '32102397',
            'ext': 'mp3',
            'title': 'Bad Blood (feat. Kendrick Lamar)',
            'creator': 'Taylor Swift / Kendrick Lamar',
            'upload_date': '20150517',
            'timestamp': 1431878400,
            'subtitles': {
                'origin': [{'ext': 'lrc', 'data': 'md5:eb9ae90502b435de7d9e99fc7602adb4'}],
                'translated': [{'ext': 'lrc', 'data': 'md5:cadca69fdfb7b679d273cc01a518f7dd'}],
            }
        },
    }, {
        'note': 'No lyrics translation.',
        'url': 'http://music.163.com/#/song?id=29822014',
        'info_dict': {
            'id': '29822014',
            'ext': 'mp3',
            'title': '听见下雨的声音',
            'creator': '周杰伦',
            'upload_date': '20141225',
            'timestamp': 1419523200,
            'subtitles': {
                'origin': [{'ext': 'lrc', 'data': 'md5:a1766edaa6dbc85357f0ae9feabc867b'}],
            }
        },
    }, {
        'note': 'No lyrics.',
        'url': 'http://music.163.com/song?id=17241424',
        'info_dict': {
            'id': '17241424',
            'ext': 'mp3',
            'title': 'Opus 28',
            'creator': 'Dustin O\'Halloran',
            'upload_date': '20080211',
            'timestamp': 1202745600,
            'subtitles': {}
        },
    }, {
        'note': 'Has translated name.',
        'url': 'http://music.163.com/#/song?id=22735043',
        'info_dict': {
            'id': '22735043',
            'ext': 'mp3',
            'title': '소원을 말해봐 (Genie)',
            'creator': '少女时代',
            'upload_date': '20100127',
            'timestamp': 1264608000,
            'alt_title': '说出愿望吧(Genie)',
            'subtitles': {
                'origin': [{'ext': 'lrc', 'data': 'md5:8d5782f92bb275b9a6acd01e9ffd12b9'}],
                'translated': [{'ext': 'lrc', 'data': 'md5:d8270e3375fd305f92b18ad78585cabb'}],
            }
        }
    }, {
        'note': 'some lines with multiple time tag',
        'url': 'http://music.163.com/#/song?id=4926366',
        'info_dict': {
            'id': '4926366',
            'ext': 'mp3',
            'title': 'sweet&sweet holiday',
            'timestamp': 1306252800,
            'upload_date': '20110524',
            'subtitles': {
                'origin': [{'ext': 'lrc', 'data': 'md5:9971db3f0361b0b66d47ba5c95bbff35'}],
                'translated': [{'ext': 'lrc', 'data': 'md5:ce5f9eef13ae4948b01bbb015fc507e1'}],
            }
        }
    }, {
        'note': 'some lines with multiple time tag and time need to be fixed',
        'url': 'http://music.163.com/#/song?id=22826396',
        'info_dict': {
            'id': '22826396',
            'ext': 'mp3',
            'title': 'God knows...',
            'timestamp': 1306252800,
            'upload_date': '20110524',
            'subtitles': {
                'origin': [{'ext': 'lrc', 'data': 'md5:5ca2952ed8974f2c28beb1c0f89e2ab5'}],
                'translated': [{'ext': 'lrc', 'data': 'md5:5ed0d4adb337594f927674d351ba6626'}],
            }
        }
    }]

    def _fix_timestamp(self, timestamp):
        # Netease returns timestamp use 2 or 3 digits for less than
        # 1 second metrics
        # While standard LRC requires exact 2 digits
        # remvoe the 3rd digit if the there're three
        match_expr = r'\[([0-9]{2}:[0-9]{2}\.[0-9]{2})(.*)\]'
        match_result = re.match(match_expr, timestamp)
        if match_result:
            # This must match as match_expr is exact the first group of lyrics_expr
            return '[' + match_result.group(1) + ']'
        else:
            # return a valid timestamp to avoid other applications' error
            return '[00:00.00]'

    def _fix_lyric_timestamp(self, line):
        text = line
        corrected_times = ''
        lyrics_expr = r'(\[[0-9]{2}:[0-9]{2}\.[0-9]{2,}\])([^\n]*)'
        # Handle time tag with one or more time in one line.
        while True:
            m = re.match(lyrics_expr, text)
            if m:
                corrected_times += self._fix_timestamp(m.group(1))
                text = m.group(2)
            else:
                break
        return corrected_times + text

    def _process_lyrics(self, lyrics_info):
        original = lyrics_info.get('lrc', {}).get('lyric')
        translated = lyrics_info.get('tlyric', {}).get('lyric')

        if not translated:
            translated = ''
        if not original:
            original = ''

        lyrics_expr = r'\[[0-9]{2}:[0-9]{2}\.[0-9]{2,}\][^\n]*'
        original_ts_texts = re.findall(lyrics_expr, original)
        translated_ts_texts = re.findall(lyrics_expr, translated)
        gen_lyrics = lambda texts: '\n'.join(map(self._fix_lyric_timestamp, texts)) + '\n' if texts else ''
        lyrics_original = gen_lyrics(original_ts_texts)
        lyrics_translated = gen_lyrics(translated_ts_texts)
        return lyrics_original, lyrics_translated

    def _real_extract(self, url):
        song_id = self._match_id(url)

        params = {
            'id': song_id,
            'ids': '[%s]' % song_id
        }
        info = self.query_api(
            'song/detail?' + compat_urllib_parse.urlencode(params),
            song_id, 'Downloading song info')['songs'][0]

        formats = self.extract_formats(info)
        self._sort_formats(formats)

        lyrics_info = self.query_api(
            'song/lyric?id=%s&lv=-1&tv=-1' % song_id,
            song_id, 'Downloading lyrics data')
        lyrics_original, lyrics_translated = self._process_lyrics(lyrics_info)

        alt_title = None
        if info.get('transNames'):
            alt_title = '/'.join(info.get('transNames'))

        ret = {
            'id': song_id,
            'title': info['name'],
            'alt_title': alt_title,
            'creator': ' / '.join([artist['name'] for artist in info.get('artists', [])]),
            'timestamp': self.convert_milliseconds(info.get('album', {}).get('publishTime')),
            'thumbnail': info.get('album', {}).get('picUrl'),
            'duration': self.convert_milliseconds(info.get('duration', 0)),
            'description': '',
            'subtitles': {},
            'formats': formats,
        }

        def update_lyrics(info_dict, key, content):
            if content:
                info_dict['subtitles'][key] = [{
                    'ext': 'lrc',
                    'data': content
                }]
        update_lyrics(ret, 'origin', lyrics_original)
        update_lyrics(ret, 'translated', lyrics_translated)
        return ret


class NetEaseMusicAlbumIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:album'
    IE_DESC = '网易云音乐 - 专辑'
    _VALID_URL = r'https?://music\.163\.com/(#/)?album\?id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://music.163.com/#/album?id=220780',
        'info_dict': {
            'id': '220780',
            'title': 'B\'day',
        },
        'playlist_count': 23,
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        info = self.query_api(
            'album/%s?id=%s' % (album_id, album_id),
            album_id, 'Downloading album data')['album']

        name = info['name']
        desc = info.get('description')
        entries = [
            self.url_result('http://music.163.com/#/song?id=%s' % song['id'],
                            'NetEaseMusic', song['id'])
            for song in info['songs']
        ]
        return self.playlist_result(entries, album_id, name, desc)


class NetEaseMusicSingerIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:singer'
    IE_DESC = '网易云音乐 - 歌手'
    _VALID_URL = r'https?://music\.163\.com/(#/)?artist\?id=(?P<id>[0-9]+)'
    _TESTS = [{
        'note': 'Singer has aliases.',
        'url': 'http://music.163.com/#/artist?id=10559',
        'info_dict': {
            'id': '10559',
            'title': '张惠妹 - aMEI;阿密特',
        },
        'playlist_count': 50,
    }, {
        'note': 'Singer has translated name.',
        'url': 'http://music.163.com/#/artist?id=124098',
        'info_dict': {
            'id': '124098',
            'title': '李昇基 - 이승기',
        },
        'playlist_count': 50,
    }]

    def _real_extract(self, url):
        singer_id = self._match_id(url)

        info = self.query_api(
            'artist/%s?id=%s' % (singer_id, singer_id),
            singer_id, 'Downloading singer data')

        name = info['artist']['name']
        if info['artist']['trans']:
            name = '%s - %s' % (name, info['artist']['trans'])
        if info['artist']['alias']:
            name = '%s - %s' % (name, ';'.join(info['artist']['alias']))

        entries = [
            self.url_result('http://music.163.com/#/song?id=%s' % song['id'],
                            'NetEaseMusic', song['id'])
            for song in info['hotSongs']
        ]
        return self.playlist_result(entries, singer_id, name)


class NetEaseMusicListIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:playlist'
    IE_DESC = '网易云音乐 - 歌单'
    _VALID_URL = r'https?://music\.163\.com/(#/)?(playlist|discover/toplist)\?id=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://music.163.com/#/playlist?id=79177352',
        'info_dict': {
            'id': '79177352',
            'title': 'Billboard 2007 Top 100',
            'description': 'md5:12fd0819cab2965b9583ace0f8b7b022'
        },
        'playlist_count': 99,
    }, {
        'note': 'Toplist/Charts sample',
        'url': 'http://music.163.com/#/discover/toplist?id=3733003',
        'info_dict': {
            'id': '3733003',
            'title': 're:韩国Melon排行榜周榜 [0-9]{4}-[0-9]{2}-[0-9]{2}',
            'description': 'md5:73ec782a612711cadc7872d9c1e134fc',
        },
        'playlist_count': 50,
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)

        info = self.query_api(
            'playlist/detail?id=%s&lv=-1&tv=-1' % list_id,
            list_id, 'Downloading playlist data')['result']

        name = info['name']
        desc = info.get('description')

        if info.get('specialType') == 10:  # is a chart/toplist
            datestamp = datetime.fromtimestamp(
                self.convert_milliseconds(info['updateTime'])).strftime('%Y-%m-%d')
            name = '%s %s' % (name, datestamp)

        entries = [
            self.url_result('http://music.163.com/#/song?id=%s' % song['id'],
                            'NetEaseMusic', song['id'])
            for song in info['tracks']
        ]
        return self.playlist_result(entries, list_id, name, desc)


class NetEaseMusicMvIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:mv'
    IE_DESC = '网易云音乐 - MV'
    _VALID_URL = r'https?://music\.163\.com/(#/)?mv\?id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://music.163.com/#/mv?id=415350',
        'info_dict': {
            'id': '415350',
            'ext': 'mp4',
            'title': '이럴거면 그러지말지',
            'description': '白雅言自作曲唱甜蜜爱情',
            'creator': '白雅言',
            'upload_date': '20150520',
        },
    }

    def _real_extract(self, url):
        mv_id = self._match_id(url)

        info = self.query_api(
            'mv/detail?id=%s&type=mp4' % mv_id,
            mv_id, 'Downloading mv info')['data']

        formats = [
            {'url': mv_url, 'ext': 'mp4', 'format_id': '%sp' % brs, 'height': int(brs)}
            for brs, mv_url in info['brs'].items()
        ]
        self._sort_formats(formats)

        return {
            'id': mv_id,
            'title': info['name'],
            'description': info.get('desc') or info.get('briefDesc'),
            'creator': info['artistName'],
            'upload_date': info['publishTime'].replace('-', ''),
            'formats': formats,
            'thumbnail': info.get('cover'),
            'duration': self.convert_milliseconds(info.get('duration', 0)),
        }


class NetEaseMusicProgramIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:program'
    IE_DESC = '网易云音乐 - 电台节目'
    _VALID_URL = r'https?://music\.163\.com/(#/?)program\?id=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://music.163.com/#/program?id=10109055',
        'info_dict': {
            'id': '10109055',
            'ext': 'mp3',
            'title': '不丹足球背后的故事',
            'description': '喜马拉雅人的足球梦 ...',
            'creator': '大话西藏',
            'timestamp': 1434179342,
            'upload_date': '20150613',
            'duration': 900,
        },
    }, {
        'note': 'This program has accompanying songs.',
        'url': 'http://music.163.com/#/program?id=10141022',
        'info_dict': {
            'id': '10141022',
            'title': '25岁，你是自在如风的少年<27°C>',
            'description': 'md5:8d594db46cc3e6509107ede70a4aaa3b',
        },
        'playlist_count': 4,
    }, {
        'note': 'This program has accompanying songs.',
        'url': 'http://music.163.com/#/program?id=10141022',
        'info_dict': {
            'id': '10141022',
            'ext': 'mp3',
            'title': '25岁，你是自在如风的少年<27°C>',
            'description': 'md5:8d594db46cc3e6509107ede70a4aaa3b',
            'timestamp': 1434450841,
            'upload_date': '20150616',
        },
        'params': {
            'noplaylist': True
        }
    }]

    def _real_extract(self, url):
        program_id = self._match_id(url)

        info = self.query_api(
            'dj/program/detail?id=%s' % program_id,
            program_id, 'Downloading program info')['program']

        name = info['name']
        description = info['description']

        if not info['songs'] or self._downloader.params.get('noplaylist'):
            if info['songs']:
                self.to_screen(
                    'Downloading just the main audio %s because of --no-playlist'
                    % info['mainSong']['id'])

            formats = self.extract_formats(info['mainSong'])
            self._sort_formats(formats)

            return {
                'id': program_id,
                'title': name,
                'description': description,
                'creator': info['dj']['brand'],
                'timestamp': self.convert_milliseconds(info['createTime']),
                'thumbnail': info['coverUrl'],
                'duration': self.convert_milliseconds(info.get('duration', 0)),
                'formats': formats,
            }

        self.to_screen(
            'Downloading playlist %s - add --no-playlist to just download the main audio %s'
            % (program_id, info['mainSong']['id']))

        song_ids = [info['mainSong']['id']]
        song_ids.extend([song['id'] for song in info['songs']])
        entries = [
            self.url_result('http://music.163.com/#/song?id=%s' % song_id,
                            'NetEaseMusic', song_id)
            for song_id in song_ids
        ]
        return self.playlist_result(entries, program_id, name, description)


class NetEaseMusicDjRadioIE(NetEaseMusicBaseIE):
    IE_NAME = 'netease:djradio'
    IE_DESC = '网易云音乐 - 电台'
    _VALID_URL = r'https?://music\.163\.com/(#/)?djradio\?id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://music.163.com/#/djradio?id=42',
        'info_dict': {
            'id': '42',
            'title': '声音蔓延',
            'description': 'md5:766220985cbd16fdd552f64c578a6b15'
        },
        'playlist_mincount': 40,
    }
    _PAGE_SIZE = 1000

    def _real_extract(self, url):
        dj_id = self._match_id(url)

        name = None
        desc = None
        entries = []
        for offset in compat_itertools_count(start=0, step=self._PAGE_SIZE):
            info = self.query_api(
                'dj/program/byradio?asc=false&limit=%d&radioId=%s&offset=%d'
                % (self._PAGE_SIZE, dj_id, offset),
                dj_id, 'Downloading dj programs - %d' % offset)

            entries.extend([
                self.url_result(
                    'http://music.163.com/#/program?id=%s' % program['id'],
                    'NetEaseMusicProgram', program['id'])
                for program in info['programs']
            ])

            if name is None:
                radio = info['programs'][0]['radio']
                name = radio['name']
                desc = radio['desc']

            if not info['more']:
                break

        return self.playlist_result(entries, dj_id, name, desc)

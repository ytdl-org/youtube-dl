# coding: utf-8
from __future__ import unicode_literals

import datetime
import hashlib
import hmac
import re
import time
from urllib.parse import quote, urljoin

from .common import InfoExtractor
from ..utils import (
    url_or_none,
    int_or_none,
    try_get,
    js_to_json
)


class Zingmp3_vnIE(InfoExtractor):
    _VALID_URL = r'''(?x)^
        ((http[s]?|fpt):)\/?\/(www\.|m\.|)
        (?P<site>
            (?:(zingmp3\.vn)|
            (mp3\.zing\.vn))
        )\/(?P<type>bai-hat|video-clip|embed)\/(?P<slug>.*?)\/(?P<id>.*?)\W
        '''
    IE_NAME = 'zingmp3_vn'
    IE_DESC = 'zingmp3.vn'
    _TESTS = [{
        'url': 'https://zingmp3.vn/bai-hat/Khoc-Cung-Em-Mr-Siro-Gray-Wind/ZWBI0DFI.html',
        'info_dict': {
            'id': 'ZWBI0DFI',
            'ext': 'mp3',
            'title': 'Khóc Cùng Em',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int,
            'duration': 236,
        },
    }, {
        'url': "https://zingmp3.vn/video-clip/Em-Gi-Oi-Jack-K-ICM/ZWAEFWIF.html",
        'info_dict': {
            'id': 'ZWAEFWIF',
            'ext': 'mp4',
            'title': "Em Gì Ơi",
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int,
        }
    }, {
        "url": 'https://zingmp3.vn/video-clip/Simple-Love-Obito-Seachains-Davis/ZWAFIZAZ.html',
        'info_dict': {
            'id': 'ZWAFIZAZ',
            'ext': 'mp4',
            'title': 'Simple Love',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int
        }
    }, {
        "url": 'https://zingmp3.vn/bai-hat/Marry-You-Bruno-Mars/ZWZE8I76.html',
        'info_dict': {
            'id': 'ZWZE8I76',
            'ext': 'mp3',
            'title': "Marry You",
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int,
        }
    }, {
        'url': 'https://zingmp3.vn/bai-hat/Dap-An-Cua-Ban-A-Nhung/ZWB0OWIZ.html',
        'info_dict': {
            'id': 'ZWB0OWIZ',
            'ext': 'mp3',
            'title': "Đáp Án Của Bạn / 你的答案",
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int,
        }
    }, {
        'url': 'https://zingmp3.vn/embed/song/ZWB06FEA?start=false',
        'info_dict': {
            'id': 'ZWB06FEA',
            'ext': 'mp3',
            'title': "Life Is Good",
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': str,
            'like_count': int,
            'comment_count': int,
            'view_count': int,
        }
    }, {
        # This url can not listen or download if don't have account vip, use --cookies FILE to login
        'url': 'https://zingmp3.vn/bai-hat/The-Box-Roddy-Ricch/ZWB0ZF9Z.html',
        "only_matching": True
    }]
    _default_host = "https://zingmp3.vn/"

    def _real_extract(self, url):
        self.convert_oldDomain_to_newDomain(url)
        mobj = re.search(self._VALID_URL, url)
        video_id = mobj.group('id')
        type = mobj.group('type')
        slug = mobj.group('slug')
        return self.extract_info_media(type, slug, video_id)

    def convert_oldDomain_to_newDomain(self,url):
        if 'mp3.zing.vn' in url:
            url = url.replace('mp3.zing.vn','zingmp3.vn')
        return url
    def extract_info_media(self, type, slug, video_id):
        formats = []
        name_api = ''
        if type == 'bai-hat':
            name_api = '/song/get-song-info'
        elif type == 'embed':
            if slug and slug == 'song':
                name_api = '/song/get-song-info'
        elif type == 'video-clip':
            name_api = "/video/get-video-detail"

        api = self.get_api_with_signature(name_api=name_api, video_id=video_id)
        info = self._download_json(url_or_request=api, video_id=video_id)
        if type == 'video-clip' and not self._downloader.params.get("cookiefile"):
            # TODO: Have api can get best quality like 1080p, 720p, default if dont have VIP just 480p is best quality.
            #  If requests are continuous without downtime,
            #  you may be blocked IP for a short period of time,
            #  So => time.sleep(2)
            _api_video = """http://api.mp3.zing.vn/api/mobile/video/getvideoinfo?requestdata={"id":"%s"}"""
            _json_video = self._download_json(url_or_request=_api_video % video_id, video_id=video_id)
            info['data']['streaming']['data']['default'] = _json_video.get("source")
            time.sleep(2)

        if self._downloader.params.get("cookiefile"):
            # TODO: if have vip account can get 320 or lossless media, default is 128
            # TODO: Just support login with cookie file, use --cookies FILE.
            api_download = self.get_api_with_signature(name_api='/download/get-streamings', video_id=video_id)
            _json = self._download_json(url_or_request=api_download, video_id=video_id)
            if _json and _json.get('msg') != 'Chỉ tài khoản VIP có thể tải bài hát này':
                info['data']['streaming']['default'] = _json.get('data')

        def get_lyric(data):
            """
            - Lyric is description and subtitle for media, use --get-description or --all-subs to get.
            :param data:
            :return: str
            """
            lyric = data.get('lyric') or try_get(data, lambda x: x['lyrics'][0]['content'])
            if url_or_none(lyric):
                lyric = self._download_webpage(url_or_request=lyric, video_id=video_id)
            if lyric:
                return lyric

        def add_protocol(url):
            if not url.startswith("http"):
                return 'https:' + url
            return url

        def convert_thumbnail(url):
            if url:
                return re.sub(r'w[0-9]+', 'w1080', url)

        if info.get('msg') == 'Success':
            data = info.get('data')
            title = data.get('title')
            artists_names = data.get('artists_names')
            thumbnail = convert_thumbnail(data.get('thumbnail'))
            lyric = get_lyric(data)
            like_count = int_or_none(data.get('like'))
            comment_count = int_or_none(data.get('total_comment'))
            view_count = int_or_none(data.get('listen'))
            duration = int_or_none(data.get('duration'))
            timestamp = int_or_none(data.get('timestamp'))
            artists = [{
                "id": i.get('id'),
                "name": i.get('name'),
                'link': urljoin(self._default_host, i.get('link')),
                'thumbnail': convert_thumbnail(i.get('thumbnail')),
                'follow_count': int_or_none(i.get('follow'))
            } for i in data.get('artists', [])]
            created_at = int_or_none(data.get('created_at'))
            released_at = int_or_none(data.get('released_at'))

            streaming = data.get('streaming')

            if streaming.get('msg'):
                if type == 'video-clip':
                    stream_data = streaming.get('data', dict)
                    for protocol, stream in stream_data.items():
                        if protocol == 'default':
                            protocol = 'http'
                        for quality, url in stream.items():
                            if url:
                                if protocol == 'hls':
                                    m3u8_url = add_protocol(url)
                                    m3u8_doc = self._download_webpage(m3u8_url, video_id)
                                    m3u8 = self._parse_m3u8_formats(m3u8_doc, m3u8_url)
                                    for i in m3u8:
                                        i['ext'] = "mp4"
                                    formats.extend(m3u8)
                                elif protocol == 'http':
                                    formats.append({
                                        'url': add_protocol(url),
                                        'ext': 'mp4',
                                        'protocol': protocol,
                                        'height': int_or_none(quality) or int_or_none(quality[:-1])
                                    })
                    formats = sorted(formats, key=lambda x: x['height'])
                else:
                    if streaming.get('msg') != "Success":
                        self.to_screen(
                            f"   - {self.IE_NAME} requires authentication.\n"
                            f"\t\t- Because This media need VIP account to listen or watch.\n"
                            f"\t\t- You may want to use --cookies.\n\n"
                        )
                        return
                    default = streaming.get('default')
                    for quality, url in default.items():
                        if url:
                            if quality == 'lossless':
                                formats.append({
                                    'url': add_protocol(url),
                                    'ext': 'flac',
                                    'protocol': 'http'
                                })
                            else:
                                formats.append({
                                    'url': add_protocol(url),
                                    'ext': 'mp3',
                                    'protocol': 'http'
                                })
            return {
                'id': video_id,
                'title': title,
                'artists_names': artists_names,
                'artists': artists,
                'thumbnail': thumbnail,
                'description': lyric,
                "subtitles": {
                    "lyric": [
                        {
                            "ext": "txt",
                            "data": lyric
                        }
                    ],
                },
                'created_at': created_at,
                'released_at': released_at,
                'like_count': like_count,
                'comment_count': comment_count,
                'view_count': view_count,
                'duration': duration,
                'timestamp': timestamp,
                'formats': formats
            }

    def get_api_with_signature(self, name_api, video_id='', alias='', type='', new_release=False):
        """
        - The api of this site has 1 param named sig => signature
        - It uses the hash function of the variables ctime, id, and name_api.
        - Sone api don't need id, just need ctime and name_api,
        :param name_api:
        :param video_id:
        :param type:
        :param new_release:
        :return: api
        """
        API_KEY = '38e8643fb0dc04e8d65b99994d3dafff'
        SECRET_KEY = b'10a01dcf33762d3a204cb96429918ff6'
        if not name_api:
            return

        def get_hash256(string):
            return hashlib.sha256(string.encode('utf-8')).hexdigest()

        def get_hmac512(string):
            return hmac.new(SECRET_KEY, string.encode('utf-8'), hashlib.sha512).hexdigest()

        def get_request_path(data):
            def mapping(key, value):
                return quote(key) + "=" + quote(value)

            data = [mapping(k, v) for k, v in data.items()]
            data = "&".join(data)
            return data

        def get_api_by_id(id):
            url = f"https://zingmp3.vn/api{name_api}?id={id}&"
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}id={id}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'sig': get_hmac512(f"{name_api}{sha256}")
            }
            return url + get_request_path(data)

        def get_api_chart(type):
            url = f"https://zingmp3.vn/api{name_api}?type={type}&"
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'sig': get_hmac512(f"{name_api}{sha256}")
            }
            return url + get_request_path(data)

        def get_api_new_release():
            url = f"https://zingmp3.vn/api{name_api}?"
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'sig': get_hmac512(f"{name_api}{sha256}")
            }
            return url + get_request_path(data)

        def get_api_download(id):
            url = f"https://download.zingmp3.vn/api{name_api}?id={id}&"
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}id={id}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'sig': get_hmac512(f"{name_api}{sha256}")
            }
            return url + get_request_path(data)

        def get_api_info_alias(alias):
            url = f"https://zingmp3.vn/api{name_api}?alias={alias}&"
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'sig': get_hmac512(f"{name_api}{sha256}")
            }
            return url + get_request_path(data)

        if 'download' in name_api:
            return get_api_download(id=video_id)
        if alias:
            return get_api_info_alias(alias)
        if video_id:
            return get_api_by_id(video_id)
        if type:
            return get_api_chart(type)
        if new_release:
            return get_api_new_release()
        return


class Zingmp3_vnPlaylistIE(Zingmp3_vnIE):
    IE_NAME = "zingmp3_vn:playlist"

    _VALID_URL = r'''(?x)^
    ((http[s]?|fpt):)\/?\/(www\.|m\.|)
        (?P<site>
            (?:(zingmp3\.vn)|
            (mp3\.zing\.vn))
        )\/(?P<type>album|playlist)\/(?P<slug>.*?)\/(?P<playlist_id>.*?)\W
        '''

    _TESTS = [
        {
            'url': 'https://zingmp3.vn/album/Top-100-Nhac-Hoa-Hay-NhatVarious-Artists/ZWZB96EI.html',
            "info_dict": {
                'id': "ZWZB96EI",
                'title': 'Top 100 Nhạc Hoa Hay Nhất'
            },
            "playlist_count": 100
        },
        {
            "url": "https://zingmp3.vn/album/Chi-Co-The-La-Mr-Siro-Mr-Siro/ZBWIA9DI.html",
            "info_dict": {
                "id": "ZBWIA9DI",
                "title": 'Chỉ Có Thể Là Mr Siro'
            },
            "playlist_mincount": 10
        },
        {
            'url': 'https://zingmp3.vn/playlist/Sofm-s-playlist/IWE606EA.html',
            "info_dict": {
                'id': "IWE606EA",
                'title': "Sofm's playlist"
            },
            "playlist_count": 69
        },
        {
            "url": "https://zingmp3.vn/album/Top-100-Pop-Au-My-Hay-Nhat-Various-Artists/ZWZB96AB.html",
            "info_dict": {
                "id": "ZWZB96AB",
                "title": "Top 100 Pop Âu Mỹ Hay Nhất"
            },
            "playlist_count": 100,
        }
    ]
    name_api = '/playlist/get-playlist-detail'

    def _real_extract(self, url):
        self.convert_oldDomain_to_newDomain(url)
        mobj = re.search(self._VALID_URL, url)
        playlist_id = mobj.group('playlist_id')
        return self._extract_playlist(id_playlist=playlist_id)

    def _extract_playlist(self, id_playlist):
        api = self.get_api_with_signature(name_api=self.name_api, video_id=id_playlist)
        info = self._download_json(url_or_request=api, video_id=id_playlist)
        title_playlist = try_get(info, lambda x: x['data']['title'])
        items = try_get(info, lambda x: x['data']['song']['items'])
        entries = []
        for item in items:
            url = urljoin(self._default_host, item.get('link'))
            video_id = item.get('id')
            entry = self.url_result(
                url=url,
                ie=Zingmp3_vnIE.ie_key(),
                video_id=video_id
            )
            entries.append(entry)

        return {
            '_type': 'playlist',
            'id': id_playlist,
            'title': title_playlist,
            'entries': entries,
        }


class Zingmp3_vnUserIE(Zingmp3_vnIE):
    _VALID_URL = r'''(?x)^
            ((http[s]?|fpt):)\/?\/(www\.|m\.|)
            (?P<site>
                (?:(zingmp3\.vn)|
                (mp3\.zing\.vn))
            )\/(?P<nghe_si>nghe-si\/|)
            (?P<name>.*?)
            (?:$|\/)
            (?:
                (?P<name_chu_de>.*?)\/(?P<id_chu_de>.*?\.)
                |
                (?P<slug_name>.*?$)
            )
            '''
    IE_NAME = "zingmp3_vn:user"
    _TESTS = [
        {
            "url": "https://zingmp3.vn/Mr-Siro",
            "info_dict": {
                "id": "IWZ98609",
                "title": "Mr-Siro-bai-hat"
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/onlyc",
            "info_dict": {
                "id": "IWZ9ZED8",
                "title": 'onlyc-bai-hat'
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/nghe-si/Huong-Giang-Idol",
            "info_dict": {
                "id": "IWZ9CUWA",
                "title": "Huong-Giang-Idol-bai-hat"
            },
            "playlist_mincount": 5
        },
        {
            'url': "https://zingmp3.vn/nghe-si/Huong-Giang-Idol/bai-hat",
            "info_dict": {
                "id": "IWZ9CUWA",
                "title": "Huong-Giang-Idol-bai-hat",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/nghe-si/Huong-Giang-Idol/album",
            "info_dict": {
                "id": "IWZ9CUWA",
                "title": "Huong-Giang-Idol-album",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/nghe-si/Huong-Giang-Idol/video",
            "info_dict": {
                "id": "IWZ9CUWA",
                "title": "Huong-Giang-Idol-video"
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/Mr-Siro/bai-hat",
            "info_dict": {
                "id": "IWZ98609",
                "title": "Mr-Siro-bai-hat",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/Mr-Siro/playlist",
            "info_dict": {
                "id": "IWZ98609",
                "title": "Mr-Siro-playlist",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/Mr-Siro/video",
            "info_dict": {
                "id": "IWZ98609",
                "title": "Mr-Siro-video",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://zingmp3.vn/chu-de/Acoustic/IWZ977C8.html",
            "info_dict": {
                "id": "IWZ977C8",
                "title": "Acoustic",
            },
            "playlist_mincount": 3
        }
    ]
    list_name_api_user = {
        'bai-hat': "/song/get-list",
        "playlist": "/playlist/get-list",
        "album": "/playlist/get-list",
        "video": "/video/get-list",
    }

    def _real_extract(self, url):
        self.convert_oldDomain_to_newDomain(url)
        mobj = re.search(self._VALID_URL, url)
        name = mobj.group('name')
        slug_name = mobj.group('slug_name')
        nghe_si = mobj.group('nghe_si')
        if not slug_name:
            slug_name = "bai-hat"

        name_api = self.list_name_api_user.get(slug_name) or None
        self.id_artist = None
        if nghe_si:
            webpage = self._download_webpage(url_or_request=f"https://mp3.zing.vn/nghe-si/{name}", video_id=name)
            self.id_artist = self._search_regex(r'''(?x)
                                    \<a.*?tracking=\"\_frombox=artist_artistfollow\"
                                        \s+data-id=\"(?P<id_artist>.*?)\"
                                        \s+data-type=\"(?P<data_type>.*?)\"
                                        \s+data-name=\"(?P<data_name>.*?)\".*?\>
                                        ''', webpage, "artist id", group="id_artist")
        else:
            api = self.get_api_with_signature(name_api="/oa/get-artist-info", alias=name)
            info = self._download_json(url_or_request=api, video_id=name)
            if info.get('msg') == 'Success':
                self.id_artist = try_get(info, lambda x: x['data']['artist_id'])

        if self.id_artist:
            self.api = self.get_api_with_signature(name_api=name_api, video_id=self.id_artist)
            return self.playlist_result(
                entries=self._entries(),
                playlist_id=self.id_artist,
                playlist_title=f"{name}-{slug_name}"
            )
        elif name == 'chu-de':
            self.IE_NAME = "zingmp3_vn:chu-de"
            name_chu_de = mobj.group('name_chu_de')
            self.id_chu_de = mobj.group('id_chu_de')
            self.api = self.get_api_with_signature(name_api="/topic/get-detail", video_id=self.id_chu_de)
            return self.playlist_result(
                entries=self._entries_for_chu_de(),
                playlist_id=self.id_chu_de,
                playlist_title=name_chu_de,
            )

    def _entries_for_chu_de(self):
        info = self._download_json(url_or_request=self.api, video_id=self.id_chu_de)
        if info.get('msg') != "Success":
            return
        items = try_get(info, lambda x: x['data']['playlist']['items'])
        for item in items:
            url = urljoin(self._default_host, item.get('link'))
            media_id = item.get('id')
            if 'album' in url or 'playlist' in url:
                name_api = '/playlist/get-playlist-detail'
                api = self.get_api_with_signature(name_api=name_api, video_id=media_id)
                info_playlist = self._download_json(url_or_request=api, video_id=media_id)
                items_playlist = try_get(info_playlist, lambda x: x['data']['song']['items'])
                for item_pl in items_playlist:
                    url = urljoin(self._default_host, item_pl.get('link'))
                    video_id = item_pl.get('id')
                    yield self.url_result(
                        url=url,
                        ie=Zingmp3_vnIE.ie_key(),
                        video_id=video_id
                    )

    def _entries(self):
        start = 0
        count = 30
        while True:
            info = self._download_json(url_or_request=self.api, video_id=self.id_artist, query={
                'type': 'artist',
                'start': start,
                'count': count,
                'sort': 'hot'
            })
            if info.get('msg').lower() != "success":
                break
            items = try_get(info, lambda x: x['data']['items'])
            for item in items:
                url = urljoin(self._default_host, item.get('link'))
                media_id = item.get('id')
                if 'album' in url or 'playlist' in url:
                    name_api = '/playlist/get-playlist-detail'
                    api = self.get_api_with_signature(name_api=name_api, video_id=media_id)
                    info_playlist = self._download_json(url_or_request=api, video_id=media_id)
                    items_playlist = try_get(info_playlist, lambda x: x['data']['song']['items'])
                    for item_pl in items_playlist:
                        url = urljoin(self._default_host, item_pl.get('link'))
                        video_id = item_pl.get('id')
                        yield self.url_result(
                            url=url,
                            ie=Zingmp3_vnIE.ie_key(),
                            video_id=video_id
                        )
                else:
                    yield self.url_result(
                        url=url,
                        ie=Zingmp3_vnIE.ie_key(),
                        video_id=media_id
                    )
            total = int_or_none(try_get(info, lambda x: x['data']['total']))
            start += count

            if total <= start:
                break


class Zingmp3_vnChartIE(Zingmp3_vnIE):
    IE_NAME = "zingmp3_vn:#zingchart"
    _VALID_URL = r'''(?x)^
            ((http[s]?|fpt):)\/?\/(www\.|m\.|)
            (?P<site>
                (?:(zingmp3\.vn)|
                (mp3\.zing\.vn))
            )\/(?P<name>zing-chart-tuan|zing-chart|top-new-release)\/
            (?P<slug_name>.*?)(\.|\/)(?P<id_name>.*?\.)?
            '''
    _TESTS = [
        {
            "url": "https://zingmp3.vn/zing-chart/bai-hat.html",
            "info_dict": {
                "title": "zing-chart-bai-hat",
            },
            "playlist_count": 100
        },
        {
            "url": "https://zingmp3.vn/zing-chart/video.html",
            "info_dict": {
                "title": "zing-chart-video",
            },
            "playlist_count": 100
        },
        {
            "url": "https://zingmp3.vn/zing-chart-tuan/bai-hat-US-UK/IWZ9Z0BW.html",
            "info_dict": {
                "title": "zing-chart-tuan-bai-hat-US-UK"
            },
            "playlist_mincount": 20
        },
        {
            "url": "https://zingmp3.vn/zing-chart-tuan/video-Kpop/IWZ9Z0BZ.html",
            "info_dict": {
                "title": "zing-chart-tuan-video-Kpop"
            },
            "playlist_mincount": 20
        },
        {
            "url": "https://zingmp3.vn/top-new-release/index.html",
            "info_dict": {
                "title": "top-new-release-index"
            },
            "playlist_count": 100
        }
    ]
    list_name_api = {
        'zing-chart': {
            'name': '/chart-realtime/get-detail',
            'bai-hat': 'song',
            'index': 'song',
            'video': 'video',
        },
        'zing-chart-tuan': {
            'name': '/chart/get-chart',
        },
        'top-new-release': {
            'name': '/chart/get-chart-new-release'
        }
    }

    def _real_extract(self, url):
        self.convert_oldDomain_to_newDomain(url)
        mobj = re.search(self._VALID_URL, url)
        name = mobj.group('name')
        slug_name = mobj.group('slug_name')

        if name == 'zing-chart':
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                type=self.list_name_api.get(name).get(slug_name)
            )
        elif name == 'zing-chart-tuan':
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                video_id=mobj.group('id_name')
            )
        else:
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                new_release=True
            )
        webpage = self._download_webpage(url_or_request=api, video_id=name)
        info = self._parse_json(webpage, name, transform_source=js_to_json)
        return self.playlist_result(
            entries=self._entries(try_get(info, lambda x: x['data']['items'])),
            playlist_title=f"{name}-{slug_name}"
        )

    def _entries(self, items):
        for item in items:
            url = urljoin(self._default_host, item.get('link'))
            video_id = item.get('id')
            yield self.url_result(url, ie=Zingmp3_vnIE.ie_key(), video_id=video_id)

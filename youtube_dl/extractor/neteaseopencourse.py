# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor

from ..compat import compat_str

from ..utils import ExtractorError

FORMATS = [
    'mp4Hd',
    'mp4Sd',
    'mp4Shd',
    'mp4Share',
    'm3u8Hd',
    'm3u8Sd',
    'm3u8Shd',
]

HEADERS = {
    'User-Agent':
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Mobile Safari/537.36',
}


def _make_headers(plid, rid=None):
    headers = {
        'Referer': 'http://m.open.163.com/movie?plid=%s%s' %
                   (plid, '&rid=%s' % rid if rid else '')
    }
    headers.update(HEADERS)
    return headers


class Dict(object):

    def __init__(self, **kwargs):
        self.__dict__['_dict'] = kwargs

    def __setattr__(self, key, value):
        self._dict[key] = value

    def __getattr__(self, key):
        return self._dict.get(key)

    def feed(self, **kwargs):
        self._dict.update(kwargs)

    def get_dict(self):

        def dp(obj):
            if isinstance(obj, Dict):
                return obj.get_dict()
            elif isinstance(obj, list):
                return [dp(item) for item in obj]
            else:
                return obj

        return dict([(key, dp(value)) for key, value in self._dict.items()])


class NeteaseOpenCourseBaseIE(InfoExtractor):
    IE_DESC = '网易公开课'
    _GEO_COUNTRIES = ['CN']

    def _match_ids(self, url):
        m = re.match(self._VALID_URL, url)
        plid = m.group('plid')
        rid = m.group('rid')
        return plid, rid

    def _extract_playlist(self, plid, rid=None):
        url = 'http://c.open.163.com/mob/%s/getMoviesForAndroid.do' % plid
        headers = _make_headers(plid, rid)

        js = self._download_json(url, None, headers=headers)
        if js.get('code') != 200:
            raise ExtractorError(
                '%s returned error: %s' % (url, json.dumps(js, ensure_ascii=False))
            )

        data = js['data']

        entries = []
        for video_info in data['videoList']:
            formats = []
            for fmt in FORMATS:
                if fmt == 'mp4Share':
                    url = video_info[fmt + 'Url']
                    size = None
                else:
                    url = video_info[fmt + 'UrlOrign']
                    size = video_info[fmt + 'SizeOrign']

                if not url:
                    continue

                formats.append(
                    dict(
                        format_id=video_info['mid'],
                        url=url.replace('http://', 'https://'),
                        ext='mp4' if fmt.startswith('mp4') else 'm3u8',
                        filesize=size
                    )
                )
            self._sort_formats(formats)

            subtitles = {}
            for sub in video_info['subList']:
                if not sub['subUrl']:
                    continue
                subtitle = [{'ext': 'str', 'url': sub['subUrl']}]
                subtitles[compat_str(sub['subName']).strip()] = subtitle

            entry = Dict(
                id=video_info['mid'],
                title=compat_str(video_info['title']).strip(),
                formats=formats,
                subtitles=subtitles,
                webpage_url=video_info['webUrl']
            )
            entries.append(entry)

        title = ('[%s] ' % data['type'] if data['type'] else '') + data['title'] \
            + (' by %s' % data['director'] if data['director'] else '')
        playlist = Dict(
            id=plid,
            title=compat_str(title).strip(),
            description=compat_str(data['description']).strip(),
            entries=entries
        )

        return playlist


class NeteaseOpenCourseVideoIE(NeteaseOpenCourseBaseIE):
    _VALID_URL = r'https?://open\.163\.com/movie/.+?/(?P<plid>\w+?)_(?P<rid>\w+?)\.html'
    IE_DESC = 'Netease Open Course Video Web'
    _TESTS = [
        {
            'url': 'http://open.163.com/movie/2009/10/A/O/M7ERNMNM3_M7EU4GCAO.html',
            'params': {
                'skip_download': True,
                'format': 'mp4'
            },
            'info_dict': {
                'id': 'M7EU4GCAO',
                'ext': 'mp4',
                'title': '什么是代数？',
                'webpage_url': 'http://open.163.com/movie/2009/10/A/O/M7ERNMNM3_M7EU4GCAO.html'
            }
        },
        {
            'url': 'http://open.163.com/movie/2006/1/1/9/M6HV755O6_M6HV8DF19.html',
            'params': {
                'skip_download': True,
                'format': 'mp4'
            },
            'info_dict': {
                'id': 'M6HV755O6',
                'ext': 'mp4',
                'title': '什么是积极心理学？',
                'webpage_url': 'http://open.163.com/movie/2006/1/1/9/M6HV755O6_M6HV8DF19.html'
            }
        }
    ]

    def _real_extract(self, url):
        plid, rid = self._match_ids(url)
        playlist = self._extract_playlist(plid, rid)
        for entry in playlist.entries:
            if entry.id == rid:
                return entry.get_dict()


class NeteaseOpenCourseVideoH5IE(NeteaseOpenCourseBaseIE):
    _VALID_URL = r'https?://m\.open\.163\.com/movie\?plid=(?P<plid>\w+?)&rid=(?P<rid>[^&]+)'
    IE_DESC = 'Netease Open Course Video H5'
    _TESTS = [
        {
            'url': 'http://m.open.163.com/movie?plid=M7ERNMNM3&rid=M7EU4GCAO',
            'params': {
                'skip_download': True,
                'format': 'mp4'
            },
            'info_dict': {
                'id': 'M7EU4GCAO',
                'ext': 'mp4',
                'title': '什么是代数？',
                'webpage_url': 'http://open.163.com/movie/2009/10/A/O/M7ERNMNM3_M7EU4GCAO.html'
            }
        },
        {
            'url': 'http://m.open.163.com/movie?plid=M6HV755O6&rid=M6HV8DF19',
            'params': {
                'skip_download': True,
                'format': 'mp4'
            },
            'info_dict': {
                'id': 'M6HV755O6',
                'ext': 'mp4',
                'title': '什么是积极心理学？',
                'webpage_url': 'http://open.163.com/movie/2006/1/1/9/M6HV755O6_M6HV8DF19.html',
            }
        }
    ]

    def _real_extract(self, url):
        plid, rid = self._match_ids(url)
        playlist = self._extract_playlist(plid, rid)
        for entry in playlist.entries:
            if entry.id == rid:
                return entry.get_dict()


class NeteaseOpenCoursePlaylistIE(NeteaseOpenCourseBaseIE):
    _VALID_URL = r'https?://open\.163\.com/special/.+'
    IE_DESC = 'Netease Open Course Video Playlist'
    _TESTS = [
        {
            'url': 'http://open.163.com/special/opencourse/latrobe.html',
            'info_dict':
                {
                    'id':
                        'M7ERNMNM3',
                    'title':
                        '[数理] 拉筹伯大学：无处不在的代数学 by Marcel Jackson',
                    'description':
                        '提到数学就“先炸为敬”各位，这个代数学教你买咖啡、整理信息和安排日程喔~代数和现实生活的结合，能帮你提升兴趣。不过呐，这门课还是比较适合数学大拿和学霸……'
                },
            'playlist_count': 6,
        },
        {
            'url': 'http://open.163.com/special/opencourse/positivepsychology.html',
            'info_dict':
                {
                    'id':
                        'M6HV755O6',
                    'title':
                        '[心理学] 哈佛大学公开课：幸福课 by TalBen Shahar',
                    'description':
                        '我们来到这个世上，到底追求什么才是最重要的？他坚定地认为：幸福感是衡量人生的唯一标准，是所有目标的最终目标。塔尔博士在哈佛学生中享有很高的声誉，受到学生们的爱戴与敬仰，被誉为"最受欢迎讲师"和"人生导师"。'
                },
            'playlist_count': 23,
        }
    ]

    def _real_extract(self, url):
        html = self._download_webpage(url, None, headers=HEADERS)
        m = re.search(r"_play\s*=\s*{id\s*:\s*'(?P<plid>.+?)'", html)
        if not m:
            raise ExtractorError('%s can not get plid' % url)
        plid = m.group('plid')
        playlist = self._extract_playlist(plid)
        return self.playlist_result(
            [item.get_dict() for item in playlist.entries],
            playlist_id=playlist.id,
            playlist_title=playlist.title,
            playlist_description=playlist.description
        )

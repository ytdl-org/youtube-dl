# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import (
    get_element_by_id,
    clean_html,
    ExtractorError,
    remove_start,
)


class KuwoBaseIE(InfoExtractor):
    _FORMATS = [
        {'format': 'ape', 'ext': 'ape', 'preference': 100},
        {'format': 'mp3-320', 'ext': 'mp3', 'br': '320kmp3', 'abr': 320, 'preference': 80},
        {'format': 'mp3-192', 'ext': 'mp3', 'br': '192kmp3', 'abr': 192, 'preference': 70},
        {'format': 'mp3-128', 'ext': 'mp3', 'br': '128kmp3', 'abr': 128, 'preference': 60},
        {'format': 'wma', 'ext': 'wma', 'preference': 20},
        {'format': 'aac', 'ext': 'aac', 'abr': 48, 'preference': 10}
    ]

    def _get_formats(self, song_id):
        formats = []
        for file_format in self._FORMATS:
            song_url = self._download_webpage(
                'http://antiserver.kuwo.cn/anti.s?format=%s&br=%s&rid=MUSIC_%s&type=convert_url&response=url' %
                (file_format['ext'], file_format.get('br', ''), song_id),
                song_id, note='Download %s url info' % file_format['format'],
            )
            if song_url.startswith('http://') or song_url.startswith('https://'):
                formats.append({
                    'url': song_url,
                    'format_id': file_format['format'],
                    'format': file_format['format'],
                    'preference': file_format['preference'],
                    'abr': file_format.get('abr'),
                })
        self._sort_formats(formats)
        return formats


class KuwoIE(KuwoBaseIE):
    IE_NAME = 'kuwo:song'
    IE_DESC = '酷我音乐'
    _VALID_URL = r'http://www\.kuwo\.cn/yinyue/(?P<id>\d+?)/'
    _TESTS = [{
        'url': 'http://www.kuwo.cn/yinyue/635632/',
        'info_dict': {
            'id': '635632',
            'ext': 'ape',
            'title': '爱我别走',
            'creator': '张震岳',
            'upload_date': '20080122',
            'description': 'md5:ed13f58e3c3bf3f7fd9fbc4e5a7aa75c'
        },
        'skip': 'this song has been offline because of copyright issues',
    }, {
        'url': 'http://www.kuwo.cn/yinyue/6446136/',
        'info_dict': {
            'id': '6446136',
            'ext': 'mp3',
            'title': '心',
            'creator': 'IU',
            'upload_date': '20150518',
        },
        'params': {
            'format': 'mp3-320'
        },
    }]

    def _real_extract(self, url):
        song_id = self._match_id(url)
        webpage = self._download_webpage(
            url, song_id, note='Download song detail info',
            errnote='Unable to get song detail info')
        if '对不起，该歌曲由于版权问题已被下线，将返回网站首页' in webpage:
            raise ExtractorError('this song has been offline because of copyright issues', expected=True)

        song_name = self._html_search_regex(
            r'(?s)class="(?:[^"\s]+\s+)*title(?:\s+[^"\s]+)*".*?<h1[^>]+title="([^"]+)"', webpage, 'song name')
        singer_name = self._html_search_regex(
            r'<div[^>]+class="s_img">\s*<a[^>]+title="([^>]+)"',
            webpage, 'singer name', fatal=False)
        lrc_content = clean_html(get_element_by_id('lrcContent', webpage))
        if lrc_content == '暂无':     # indicates no lyrics
            lrc_content = None

        formats = self._get_formats(song_id)

        album_id = self._html_search_regex(
            r'<p[^>]+class="album"[^<]+<a[^>]+href="http://www\.kuwo\.cn/album/(\d+)/"',
            webpage, 'album id', fatal=False)

        publish_time = None
        if album_id is not None:
            album_info_page = self._download_webpage(
                'http://www.kuwo.cn/album/%s/' % album_id, song_id,
                note='Download album detail info',
                errnote='Unable to get album detail info')

            publish_time = self._html_search_regex(
                r'发行时间：(\d{4}-\d{2}-\d{2})', album_info_page,
                'publish time', fatal=False)
            if publish_time:
                publish_time = publish_time.replace('-', '')

        return {
            'id': song_id,
            'title': song_name,
            'creator': singer_name,
            'upload_date': publish_time,
            'description': lrc_content,
            'formats': formats,
        }


class KuwoAlbumIE(InfoExtractor):
    IE_NAME = 'kuwo:album'
    IE_DESC = '酷我音乐 - 专辑'
    _VALID_URL = r'http://www\.kuwo\.cn/album/(?P<id>\d+?)/'
    _TEST = {
        'url': 'http://www.kuwo.cn/album/502294/',
        'info_dict': {
            'id': '502294',
            'title': 'M',
            'description': 'md5:6a7235a84cc6400ec3b38a7bdaf1d60c',
        },
        'playlist_count': 2,
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        webpage = self._download_webpage(
            url, album_id, note='Download album info',
            errnote='Unable to get album info')

        album_name = self._html_search_regex(
            r'<div[^>]+class="comm"[^<]+<h1[^>]+title="([^"]+)"', webpage,
            'album name')
        album_intro = remove_start(
            clean_html(get_element_by_id('intro', webpage)),
            '%s简介：' % album_name)

        entries = [
            self.url_result(song_url, 'Kuwo') for song_url in re.findall(
                r'<p[^>]+class="listen"><a[^>]+href="(http://www\.kuwo\.cn/yinyue/\d+/)"',
                webpage)
        ]
        return self.playlist_result(entries, album_id, album_name, album_intro)


class KuwoChartIE(InfoExtractor):
    IE_NAME = 'kuwo:chart'
    IE_DESC = '酷我音乐 - 排行榜'
    _VALID_URL = r'http://yinyue\.kuwo\.cn/billboard_(?P<id>[^.]+).htm'
    _TEST = {
        'url': 'http://yinyue.kuwo.cn/billboard_香港中文龙虎榜.htm',
        'info_dict': {
            'id': '香港中文龙虎榜',
            'title': '香港中文龙虎榜',
            'description': 're:\d{4}第\d{2}期',
        },
        'playlist_mincount': 10,
    }

    def _real_extract(self, url):
        chart_id = self._match_id(url)
        webpage = self._download_webpage(
            url, chart_id, note='Download chart info',
            errnote='Unable to get chart info')

        chart_name = self._html_search_regex(
            r'<h1[^>]+class="unDis">([^<]+)</h1>', webpage, 'chart name')

        chart_desc = self._html_search_regex(
            r'<p[^>]+class="tabDef">(\d{4}第\d{2}期)</p>', webpage, 'chart desc')

        entries = [
            self.url_result(song_url, 'Kuwo') for song_url in re.findall(
                r'<a[^>]+href="(http://www\.kuwo\.cn/yinyue/\d+)/"', webpage)
        ]
        return self.playlist_result(entries, chart_id, chart_name, chart_desc)


class KuwoSingerIE(InfoExtractor):
    IE_NAME = 'kuwo:singer'
    IE_DESC = '酷我音乐 - 歌手'
    _VALID_URL = r'http://www\.kuwo\.cn/mingxing/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.kuwo.cn/mingxing/bruno+mars/',
        'info_dict': {
            'id': 'bruno+mars',
            'title': 'Bruno Mars',
        },
        'playlist_count': 10,
    }, {
        'url': 'http://www.kuwo.cn/mingxing/Ali/music.htm',
        'info_dict': {
            'id': 'Ali',
            'title': 'Ali',
        },
        'playlist_mincount': 95,
        'skip': 'Regularly stalls travis build',  # See https://travis-ci.org/rg3/youtube-dl/jobs/78878540
    }]

    def _real_extract(self, url):
        singer_id = self._match_id(url)
        webpage = self._download_webpage(
            url, singer_id, note='Download singer info',
            errnote='Unable to get singer info')

        singer_name = self._html_search_regex(
            r'<div class="title clearfix">\s*<h1>([^<]+)<span', webpage, 'singer name'
        )

        entries = []
        first_page_only = False if re.search(r'/music(?:_\d+)?\.htm', url) else True
        for page_num in itertools.count(1):
            webpage = self._download_webpage(
                'http://www.kuwo.cn/mingxing/%s/music_%d.htm' % (singer_id, page_num),
                singer_id, note='Download song list page #%d' % page_num,
                errnote='Unable to get song list page #%d' % page_num)

            entries.extend([
                self.url_result(song_url, 'Kuwo') for song_url in re.findall(
                    r'<p[^>]+class="m_name"><a[^>]+href="(http://www\.kuwo\.cn/yinyue/\d+)/',
                    webpage)
            ][:10 if first_page_only else None])

            if first_page_only or not re.search(r'<a[^>]+href="[^"]+">下一页</a>', webpage):
                break

        return self.playlist_result(entries, singer_id, singer_name)


class KuwoCategoryIE(InfoExtractor):
    IE_NAME = 'kuwo:category'
    IE_DESC = '酷我音乐 - 分类'
    _VALID_URL = r'http://yinyue\.kuwo\.cn/yy/cinfo_(?P<id>\d+?).htm'
    _TEST = {
        'url': 'http://yinyue.kuwo.cn/yy/cinfo_86375.htm',
        'info_dict': {
            'id': '86375',
            'title': '八十年代精选',
            'description': '这些都是属于八十年代的回忆！',
        },
        'playlist_count': 30,
    }

    def _real_extract(self, url):
        category_id = self._match_id(url)
        webpage = self._download_webpage(
            url, category_id, note='Download category info',
            errnote='Unable to get category info')

        category_name = self._html_search_regex(
            r'<h1[^>]+title="([^<>]+?)">[^<>]+?</h1>', webpage, 'category name')

        category_desc = remove_start(
            get_element_by_id('intro', webpage).strip(),
            '%s简介：' % category_name)

        jsonm = self._parse_json(self._html_search_regex(
            r'var\s+jsonm\s*=\s*([^;]+);', webpage, 'category songs'), category_id)

        entries = [
            self.url_result('http://www.kuwo.cn/yinyue/%s/' % song['musicrid'], 'Kuwo')
            for song in jsonm['musiclist']
        ]
        return self.playlist_result(entries, category_id, category_name, category_desc)


class KuwoMvIE(KuwoBaseIE):
    IE_NAME = 'kuwo:mv'
    IE_DESC = '酷我音乐 - MV'
    _VALID_URL = r'http://www\.kuwo\.cn/mv/(?P<id>\d+?)/'
    _TEST = {
        'url': 'http://www.kuwo.cn/mv/6480076/',
        'info_dict': {
            'id': '6480076',
            'ext': 'mkv',
            'title': '我们家MV',
            'creator': '2PM',
        },
    }
    _FORMATS = KuwoBaseIE._FORMATS + [
        {'format': 'mkv', 'ext': 'mkv', 'preference': 250},
        {'format': 'mp4', 'ext': 'mp4', 'preference': 200},
    ]

    def _real_extract(self, url):
        song_id = self._match_id(url)
        webpage = self._download_webpage(
            url, song_id, note='Download mv detail info: %s' % song_id,
            errnote='Unable to get mv detail info: %s' % song_id)

        mobj = re.search(
            r'<h1[^>]+title="(?P<song>[^"]+)">[^<]+<span[^>]+title="(?P<singer>[^"]+)"',
            webpage)
        if mobj:
            song_name = mobj.group('song')
            singer_name = mobj.group('singer')
        else:
            raise ExtractorError('Unable to find song or singer names')

        formats = self._get_formats(song_id)

        return {
            'id': song_id,
            'title': song_name,
            'creator': singer_name,
            'formats': formats,
        }

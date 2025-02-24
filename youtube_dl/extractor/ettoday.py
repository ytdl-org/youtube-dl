# coding: utf-8
from __future__ import unicode_literals


import re
import unicodedata

from .common import InfoExtractor
from ..utils import (
    get_element_by_class,
    extract_attributes,
    int_or_none,
    strip_or_none,
    parse_iso8601,
    unescapeHTML,
    ExtractorError)


class EttodayIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:boba|www)\.ettoday\.net/
                    (?P<type>
                        videonews|
                        tools/player|
                        video
                    )/(?:
                        (?P<x>[0-9]+)/(?P<y>[0-9]+)/|
                        (?:[0-9]+-)
                    )?(?P<id>[0-9]+)'''
    _TESTS = [{
        'url': 'https://boba.ettoday.net/videonews/250060',
        'md5': 'd875be90d233878829d779d336e550cc',
        'info_dict': {
            'id': '250060',
            'ext': 'mp4',
            'title': '梁靜茹《勇氣》《暖暖》演唱會必聽！　「愛真的需要勇氣..」全場合唱超感人',
            'description': '梁靜茹《勇氣》《暖暖》演唱會必聽！　「愛真的需要勇氣..」全場合唱超感人',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 188,
            'timestamp': 1609088513,
            'upload_date': '20201227'
        }
    }, {
        'url': 'https://boba.ettoday.net/videonews/250575',
        'md5': 'a8a883f23809e6fd14d6ffcdc4950a2d',
        'info_dict': {
            'id': '250575',
            'ext': 'mp4',
            'title': '【料理之王】EP10精華｜亞州廚神Jason Wang指定「沙公ft.柑橘」 黃晶晶V.S洪士元',
            'description': '訂閱《料理之王》頻道:https://bit.ly/32n7bIS全新廚藝節目《料理之王》10月23日起每周五晚上九點於料理之王、播吧Youtube頻道首播。主持人：Lulu 黃路梓茵首席導師：廚佛瑞德Fred、「亞洲廚神」Jason Wang王凱傑、福原愛飛行導師：吳健豪、王輔立',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1570,
            'timestamp': 1609325661,
            'upload_date': '20201230'
        }
    }, {
        'url': 'https://www.ettoday.net/tools/player/709749-250599?title=%E5%B7%A5%E4%BA%BA%E6%89%9B%E3%80%8C9%E5%B1%A4%E6%B3%A1%E6%A3%89%E7%A3%9A%E3%80%8D%E9%9A%A8%E6%A9%9F%E5%81%87%E8%B7%8C%EF%BC%81%E8%B7%AF%E4%BA%BA%E5%85%A8%E8%B7%B3%E9%96%8B%E3%80%81%E9%98%BF%E5%AC%A4%E5%9A%87%E5%A3%9E%E9%95%B7%E9%9F%B3%E5%B0%96%E5%8F%AB&bid=boba_preroll_web&show_ad=1&uccu=3&auto',
        'md5': '14f92cdb0d535363243343542aebe121',
        'info_dict': {
            'id': '250599',
            'ext': 'mp4',
            'title': '工人扛「9層泡棉磚」隨機假跌！路人全跳開、阿嬤嚇壞長音尖叫',
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }, {
        'url': 'https://boba.ettoday.net/video/33/174/247571',
        'md5': '675178c997f644f622723749fc2f987c',
        'info_dict': {
            'id': '247571',
            'ext': 'mp4',
            'title': '慣老闆們小心!律師來教社畜面對職場不合理待遇 Ft.律師男友Joey｜回覆IG問答｜【社畜時代podcast】｜EP.03',
            'description': '社畜podcast來了 律師來幫你解答囉',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2419,
            'timestamp': 1607653880,
            'upload_date': '20201211'
        }
    }]

    def _get_preference(self, url_info):
        if (url_info.get('quality') == 'AUTO'):
            return -1
        else:
            return int(url_info.get('quality'))

    def _sanitize_control_char(self, s):
        return ''.join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    def _extract_videonews_info(self, url, video_id):
        webpage = self._download_webpage(url, video_id)

        json_data = self._search_json_ld(
            self._sanitize_control_char(webpage), video_id,
            expected_type='VideoObject', fatal=False, default={})

        title = strip_or_none(
            unescapeHTML(json_data.get('title') or self._og_search_title(webpage)))

        desc = strip_or_none(
            unescapeHTML(json_data.get('description') or self._og_search_description(webpage)))

        tb = json_data.get('thumbnail') or self._og_search_thumbnail(webpage)

        upload = int_or_none(
            json_data.get('timestamp')
            or parse_iso8601(self._html_search_meta('pubdate', webpage)))

        attrs = extract_attributes(get_element_by_class('video', webpage))

        return attrs.get('src'), {
            'title': title,
            'description': desc,
            'thumbnail': tb,
            'duration': json_data.get('duration'),
            'timestamp': upload
        }

    def _extract_toolplayer_info(self, webpage, video_id):
        title = self._html_search_regex(
            r'<title>(?P<title>.+?)</title>',
            webpage, 'title', group='title', default=None)

        tb = self._html_search_regex(
            r"setAttribute\('poster',[^\S]'(?P<thumbnail>.+?)'\)",
            webpage, 'thumbnail', group='thumbnail', default=None)

        return {
            'title': title,
            'thumbnail': tb
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page_type = self._search_regex(self._VALID_URL, url, 'page type', 'type')

        info_dict = {}
        if page_type == 'videonews' or page_type == 'video':
            src_url, info_dict = self._extract_videonews_info(url, video_id)
            content = self._download_webpage(src_url, video_id)
        elif page_type == 'tools/player':
            content = self._download_webpage(url, video_id)
            info_dict = self._extract_toolplayer_info(content, video_id)
        else:
            raise ExtractorError('Unsupported url type.')

        r = re.compile(
            r"quality !== \'(?:[0-9,A-Z]+)\'\) {[^\S]+url = \'(?P<url>[^\']+)\';[^\S]+quality = \'(?P<quality>[0-9|AUTO]{3,4})P?\';")
        urls_info = [m.groupdict() for m in r.finditer(content)]

        formats = []
        for url_info in urls_info:
            formats.extend(self._extract_m3u8_formats(
                url_info.get('url'), video_id, 'mp4',
                entry_protocol='m3u8_native', preference=self._get_preference(url_info)))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info_dict.get('title'),
            'formats': formats,
            'description': info_dict.get('description'),
            'thumbnail': info_dict.get('thumbnail'),
            'duration': info_dict.get('duration'),
            'timestamp': info_dict.get('timestamp')
        }

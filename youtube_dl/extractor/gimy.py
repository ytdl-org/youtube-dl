# coding: utf-8
from __future__ import unicode_literals


import re

from .common import InfoExtractor
from ..utils import (
    get_element_by_id,
    js_to_json,
    ExtractorError)


class GimyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gimy\.co/eps/(?P<id>[0-9,-]+)\.html'
    _TESTS = [{
        'url': 'http://gimy.co/eps/116498-1-1.html',
        'md5': '3c804e6600c466b98ac24a6f3431cafd',
        'info_dict': {
            'id': '116498-1-1',
            'ext': 'mp4',
            'title': '進擊的巨人第四季 進撃の巨人 The Final Season 第01集 - 順暢雲 - Gimy TV 劇迷',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': '動漫 進擊的巨人第四季-第01集更新至更新至04集 順暢雲 線上看，進擊的巨人第四季是日本由林祐一郎執導梶裕貴,石川由依,井上麻裏奈,神谷浩史主演參演，上映時間為2020年。主要劇情：在艾倫他們居住的帕拉迪島之外，還存在一個其他人類居住的世界。當中一個國家「瑪雷」與其他各國爆發戰爭。陷入苦戰之際，他們決定要攻進帕拉迪島，把「始祖的巨人」搶過來。在這裏又看到另一羣孩子們拼命求生存的身'
        }
    }, {
        'url': 'http://gimy.co/eps/116811-1-1.html',
        'info_dict': {
            'id': '116811-1-1',
            'ext': 'mp4',
            'title': '今際之國的闖關者 今際の国のアリス  第01集 - 光速雲 - Gimy TV 劇迷',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': '日劇 今際之國的闖關者-第01集更新至完結 光速雲 線上看，今際之國的闖關者是日本由佐藤信介,下村勇二執導山崎賢人,土屋太鳳,村上虹郎,森永悠希,三吉彩花,町田啓太,櫻田通,朝比奈彩,柳俊太郎,渡邊佑太朗,水崎綾女,吉田美月喜,阿部力,金子統昭,青柳翔,仲裏依紗主演參演，上映時間為2020年。主要劇情：有棲良平是一個無精打采、沉迷於電子遊戲的年輕無業遊民。他突然發現自己來到了一個奇怪且荒蕪的東京，他和朋友們必須在危險的遊戲中競爭求生。在這個奇怪的世界裏，有棲良平遇到了獨自應對遊戲的年輕女子宇佐木柚葉'
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://gimy.co/eps/533-1-25.html',
        'info_dict': {
            'id': '533-1-25',
            'ext': 'mp4',
            'title': '海賊王 航海王 第25集 - 光速雲 - Gimy TV 劇迷',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': '動漫 海賊王-第25集更新至更新至956集 光速雲 線上看，海賊王是日本由宮元宏彰執導田中真弓,中井和哉主演參演，上映時間為2014年。主要劇情：在故事中爲一個大祕寶之意。故事描述男主角草帽蒙其·D·路飛爲了當上海賊王而踏上偉大航道及與其夥伴的經歷。傳說中海賊王哥爾·D·傑在死前說出他留下'
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player = get_element_by_id('zanpiancms_player', webpage)
        mobj = re.search(r'player_data=(?P<urls_info>[^<]+)<', player)
        if mobj is None:
            raise ExtractorError('Unable to extract url info')

        urls_info = self._parse_json(mobj.group('urls_info'), video_id, transform_source=js_to_json)
        m3u8_url = urls_info.get('url')
        if m3u8_url is None:
            raise ExtractorError('Unable to extract video urls')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native'),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage)
        }

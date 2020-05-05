# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    int_or_none,
    parse_duration,
)


class TelegramIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?t\.me/s/(?P<id>[\s\S]+)'
    _TESTS = [
        {
            'url': 'https://t.me/s/telegram/86',
            'md5': 'afd6c7f574fead14e35ca83e3705e01d',
            'info_dict': {
                'id': 'telegram/86',
                'ext': 'mp4',
                'title': 'Telegram News – Telegram',
                'description': 'This video should give you an idea of how the new account switching feature works – available on Android today and coming soon to other platforms. ✨🌟⭐️ Happy holidays!',
                'thumbnail': 're:https://cdn(.*).telesco.pe/file/(.*)',
                'uploader': 'Telegram News',
                'upload_date': '20171230',
                'timestamp': 1514667477,
            }
        }, {
            'url': 'https://t.me/s/leehsienloong/382',
            'md5': '01559de5a145d0547f4c53bd5340549d',
            'info_dict': {
                'id': 'leehsienloong/382',
                'ext': 'mp4',
                'title': 'Lee Hsien Loong – Telegram',
                'description': 'Dropped by Sengkang West this morning to say hi to everyone, and see how residents were doing. I was happy to see many young families out spending time with their little ones!',
                'thumbnail': 're:https://cdn(.*).telesco.pe/file/(.*)',
                'uploader': 'Lee Hsien Loong',
                'upload_date': '20200315',
                'timestamp': 1584276195,
                'duration': 57,
            }
        }, {
            'url': 'https://t.me/s/durov/82',
            'only_matching': True,
        }, {
            'url': 'https://t.me/s/durov/83',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        original_webpage = self._download_webpage(url, video_id)

        this_div = self._search_regex(
            r'<div .* data-post="' + video_id + r'" .*>([\s\S]*?)</time></a>',
            original_webpage, 'pageblock')

        title = self._html_search_regex(
            r'<title>(.+?)</title>',
            original_webpage, 'title')

        description = self._html_search_regex(
            r'<div class="tgme_widget_message_text.*?>([\s\S]*?)</div>',
            this_div, 'description', default=None)

        url = self._search_regex(
            r'<video src="(.*?)"',
            this_div, None)

        thumbnail = self._search_regex(
            r"background-image:url\('([\s\S]*?)'\)",
            this_div, 'thumbnail', default=None)

        uploader = self._html_search_regex(
            r'<a class="tgme_widget_message_owner_name" .*><span dir="auto">(.*)</span>',
            this_div, 'uploader', default=None)

        timestamp = unified_timestamp(
            self._search_regex(
                r'datetime="(.*)"',
                this_div, 'upload_time', default=None)
        )

        duration = self._html_search_regex(
            r'<time class="message_video_duration.*?>(.*?)</time>',
            this_div, 'duration', default=None)
        duration = int_or_none(parse_duration(duration))

        info_dict = {
            'id': video_id,
            'title': title,
            'description': description,
            'url': url,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
        }

        return info_dict

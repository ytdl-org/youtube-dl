# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


class TelegramIE(InfoExtractor):
    _VALID_URL = r'https://t\.me/(?P<user>[^/]+)/(?P<id>\d+)'
    _TEST = {
        'url': 'https://t.me/telegram/195',
        'info_dict': {
            'id': '195',
            'ext': 'mp4',
            'title': 'telegram',
            'description': 'Telegram’s Bot Documentation has been completely overhauled –\xa0adding the latest info, along with detailed screenshots and videos.\n\nNewcomers now have an easy way to learn about all the powerful features, and can build a bot from our step-by-step tutorial with examples for popular programming languages.\n\nExperienced developers can explore recent updates and advanced features, ready for 2022 and beyond.',
            'duration': 23,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        m = re.match(r'https://t\.me/(?P<channel>[^/]+)/', url)
        if m is None:
            raise ExtractorError('Unable to find channel name')
        title = m.group('channel')
        embed_url = url + '?embed=1&mode=tme'
        html = self._download_webpage(embed_url, video_id)

        video_url = self._search_regex(r'<video src="([^"]+)"', html, 'video_url')
        formats = [{'url': video_url}]

        duration = self._search_regex(
            r'<time class="message_video_duration.*?>(\d+:\d+)<', html,
            'duration', fatal=False)
        if duration:
            try:
                mins, secs = duration.split(':')
                secs = int_or_none(secs)
                mins = int_or_none(mins)
                duration = None if secs is None or mins is None else secs + 60 * mins
            except ValueError:
                duration = None

        description = self._html_search_regex(
            r'<div class="tgme_widget_message_text.*?>(.+?)</div>', html,
            'description', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats
        }

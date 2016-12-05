# coding: utf-8
from __future__ import unicode_literals

import re
import json
import itertools
from pprint import pformat

from .common import InfoExtractor

from ..compat import compat_str

from ..utils import (
    determine_ext,
    error_to_compat_str,
    ExtractorError,
    int_or_none,
    parse_iso8601,
    sanitized_Request,
    str_to_int,
    unescapeHTML,
    mimetype2ext,
)

"""
TODO:
  * Live streams support.
  * More meta fields and comments extraction.
"""


class LineLiveBaseInfoExtractor(InfoExtractor):
    @classmethod
    def _match_channel(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        m = cls._VALID_URL_RE.match(url)
        assert m
        return m.group('channel')

    def _extract_formats(self, orig_urls):
        formats = []
        for key in orig_urls:
            if key == "abr" or key == "aac":
                """ Audio only streams, discard them """
            elif not orig_urls.get(key):
                """ null url """
            else:
                format_id = key
                url = orig_urls.get(key)
                height = int_or_none(format_id)
                ext = 'mp4'
                formats.append({
                    'format_id': format_id,
                    'format': format_id,
                    'url': url,
                    'height': height,
                    'ext': ext,
                })
        self._sort_formats(formats)
        return formats


class LineLiveIE(LineLiveBaseInfoExtractor):
    # https://live.line.me/r/channels/21/broadcast/51883
    _VALID_URL = r'(?:https?://)?live\.line\.me/channels/(?P<channel>\d+)/broadcast/(?P<id>\d+)'
    IE_NAME = 'linelive'

    _TESTS = [
        {
            'url': 'https://live.line.me/channels/27121/broadcast/38687',
            'md5': 'd4f22649557d070fa1d61be2c483819b',
            'info_dict': {
                'id': '38687',
                'ext': 'mp4',
                'title': '短時間だよライブ',
                'description': '',
                'duration': 17,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://live.line.me/channels/77/broadcast/214088',
            'md5': 'c2b16f5a530eadf57cff1b82a3eed185',
            'info_dict': {
                'id': '214088',
                'ext': 'mp4',
                'title': '12月3日 ウェザーナイトニュース',
                'description': '明日の各地のお天気をおやすみ前にお届け。\nコミューニケーション型お天気情報番組♪\n\n皆さんからのコメントも募集中！\nおやすみ前の素敵な時間をLINE LIVEで！\n\nお天気キャスター：眞家泉',
                'duration': 972,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://live.line.me/r/channels/21/broadcast/51883',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        channel = self._match_channel(url)

        info_url = "https://live-api.line-apps.com/app/v2/channel/%s/broadcast/%s" % (channel, video_id)
        info = self._download_json(info_url, video_id)

        description = info.get("description")
        item = info.get("item")
        title = ''
        if item:
            title = item.get("title")
            duration = item.get("archiveDuration")

        urls = info.get("archivedHLSURLs")
        formats = self._extract_formats(urls)

        return {
            'id': compat_str(video_id),
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
        }


# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class FczenitIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fc-zenit\.ru/video/gl(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://fc-zenit.ru/video/gl6785/',
        'md5': '458bacc24549173fe5a5aa29174a5606',
        'info_dict': {
            'id': '6785',
            'ext': 'mp4',
            'title': '«Зенит-ТВ»: как Олег Шатов играл против «Урала»',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<div class=\"photoalbum__title\">([^<]+)', webpage, 'title')

        bitrates_raw = self._html_search_regex(r'bitrates:.*\n(.*)\]', webpage, 'video URL')
        bitrates = re.findall(r'url:.?\'(.+?)\'.*?bitrate:.?([0-9]{3}?)', bitrates_raw)

        formats = [{
            'url': furl,
            'tbr': tbr,
        } for furl, tbr in bitrates]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
        }

# coding: utf-8
from __future__ import unicode_literals

from re import search
from re import findall
from .common import InfoExtractor


class GaskrankIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gaskrank\.tv/tv(?:/[^/]+)+/(?P<id>[^/]+).htm'
    _TEST = {
        'url': 'http://www.gaskrank.tv/tv/motorrad-fun/strike-einparken-durch-anfaenger-crash-mit-groesserem-flurschaden.htm',
        'md5': '1ae88dbac97887d85ebd1157a95fc4f9',
        'info_dict': {
            'id': '201601/26955',
            'ext': 'mp4',
            'title': 'Strike! Einparken können nur Männer - Flurschaden hält sich in Grenzen *lol*',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(r'https?://movies.gaskrank.tv/([^-]*?).mp4', webpage, 'video id')
        playlist = self._search_regex(r'playlist:\s*\[\s*{\s*([\s\S]*(?!}\s*]))', webpage, 'video id')
        entries = findall(r'[0-9]+:\s*{[\s\S]*?}', playlist)
        formats = []
        for entry in entries:
            format = dict()
            format['url'] = search(r'src:[\s]*\"([^\"]*)\"', entry).group(1)
            format['format_id'] = search(r'([0-9]+):\s*{[\s\S]*?}', entry).group(1)
            format['quality'] = search(r'quality:[\s]*\"([^\"]*)\"', entry).group(1)
            format['resolution'] = format['quality']
            formats.append(format)
        title = self._html_search_regex(r'movieName: *\'([^\']*)\'', webpage, 'title')
        thumbnail = self._html_search_regex(r'poster: *\'([^\']*)\'', webpage, 'thumbnail')
        categories = search(r'https?://(?:www\.)?gaskrank\.tv/tv(?:/([^/]+))+/[^/]+.htm', url).group(1)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'categories': categories,
            'display_id': display_id,
        }

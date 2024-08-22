# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import get_elements_by_class


class TASVideosIE(InfoExtractor):
    _VALID_URL = r'http://tasvideos.org/(?P<id>\d+M)\.html'
    _TEST = {
        'url': 'http://tasvideos.org/4352M.html',
        'md5': '8dced25a575e853cec5533a887a8dcfc',
        'info_dict': {
            'id': '4352M',
            'ext': 'mp4',
            'title': 'C64 L\'Abbaye des Morts',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_urls = re.findall(
            r'<a [^>]+(?P<URL>archive\.org\/download[^<]+\.(?:mkv|mp4|avi))[^<]+<\/a>',
            webpage)
        title = self._search_regex(
            r'<span title="Movie[^"]+">(?P<TITLE>[^<]+)<\/span>',
            webpage, 'title')
        time_and_author = self._html_search_regex(
            r'<th.*<\/span>(?P<time_and_author>.*)<\/th>', webpage,
            'title: speedrun timer and credit', fatal=False)
        if time_and_author is not None:
            title = title + time_and_author

        formats = []
        for url in video_urls:
            format_entry = {'url': 'http://www.' + url}
            formats.append(format_entry)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class TASVideosPlaylistIE(InfoExtractor):
    _VALID_URL = r'http://tasvideos.org/(?P<id>Movies-[^\.]*?)\.html'
    _TEST = {
        'url': 'http://tasvideos.org/Movies-Stars.html',
        'info_dict': {
            'id': 'Movies-Stars',
            'title': 'TASVideos movies: Tier Stars',
        },
        'playlist_count': 114,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        playlist_title = self._search_regex(
            r'<title>(?P<title>[^<]*)</title>', webpage, 'title')
        video_entries = get_elements_by_class('item', webpage)

        entries = []
        for entry in video_entries:
            video_urls = re.findall(
                r'<a [^>]+(?P<URL>archive\.org\/download[^<]+\.(?:mkv|mp4|avi))[^<]+<\/a>',
                entry)
            title = self._search_regex(
                r'<span title="Movie[^"]+">(?P<title>[^<]+)<\/span>',
                entry, 'title')
            time_and_author = self._html_search_regex(
                r'<th.*<\/span>(?P<time_and_author>.*)<\/th>', entry,
                'time_and_author', fatal=False)
            if time_and_author is not None:
                title = title + time_and_author
            video_id = self._search_regex(
                r'id="movie_(?P<id>\d+)', entry, 'video id') + 'M'

            formats = []
            for url in video_urls:
                format_entry = {'url': "http://www." + url}
                formats.append(format_entry)

            self._sort_formats(formats)

            formats = {
                'id': video_id,
                'title': title,
                'formats': formats,
            }
            entries.append(formats)

        return self.playlist_result(entries, playlist_id, playlist_title)

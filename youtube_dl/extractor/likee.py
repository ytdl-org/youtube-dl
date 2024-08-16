# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LikeeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?likee\.video/v/(?P<id>\w+)'
    _TEST = {
        'url': 'https://likee.video/v/k6QcOp',
        'md5': '5e0988b2ea7615075735cef87c2ca14d',
        'info_dict': {
            'id': 'k6QcOp',
            'ext': 'mp4',
            'title': 'Agua challenge     😳😱',
            'thumbnail': 'https://videosnap.like.video/na_live/3a2/1tVVI4_1.jpg?type=8',
            'uploader': 'fernanda_rivasg'
        }
    }

    def _real_initialize(self):
        # Setup session (will set necessary cookies)
        self._request_webpage(
            'https://likee.video/', None, note='Setting up session')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        # set title
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        print(title + 'f')
        # set thumbnail
        thumbnail = self._html_search_regex(r'<meta property=\"og:image\" content=\"(.+?)\">', webpage, 'thumbnail')
        # set uploader
        uploader = self._html_search_regex(r'<meta name=\"keywords\"(.+?)>', webpage, 'uploader')
        uploader = uploader.split(',')[1]
        uploader = uploader.strip()

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'ext': 'mp4',
            'url': url,
        }


class LikeeUserIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?likee\.video/p/(?P<id>\w+)'
    _TEST = {
        'url': 'https://l.likee.video/p/Gp6YGd',
        'info_dict': {
            'id': 'Gp6YGd'
        },
        'playlist_mincount': 10,
    }

    def _real_initialize(self):
        # Setup session (will set necessary cookies)
        self._request_webpage(
            'https://likee.video/', None, note='Setting up session')

    def _real_extract(self, url):
        user_id = self._match_id(url)
        webpage = self._download_webpage(url, user_id)
        current_list = self._html_search_regex(r'\"itemListElement\": \[(.+?)\]', webpage, 'baseVideoList__list')
        entries = []
        for i in range(10):
            next_result = self._html_search_regex(r'\{\"@type\":\"VideoObject\",(.+?)\},?', current_list, 'baseVideoList__list')
            entry = {}
            entry["title"] = self._html_search_regex(r'on Likee Mobile: (.+?)\"', next_result, 'title')
            temp_url = self._html_search_regex(r'\"url\":\"(.+?)\"', next_result, 'url')
            entry["url"] = temp_url.replace('\\', '')
            entry["thumbnail"] = self._html_search_regex(r'\"thumbnailUrl\":\"(.+?)\"', next_result, 'thumbnail')
            entry["uploader"] = self._html_search_regex(r'/@(.+?)\/', next_result, 'uploader')
            entry["ext"] = 'mp4'
            entry["description"] = self._html_search_regex(r'\"description\":\"(.+?)\"', next_result, 'description')
            entry["id"] = self._html_search_regex(r'\/video\\\/(.+?)\"', next_result, 'id')
            entries.append(entry)
            current_list = current_list[len(next_result):]

        return self.playlist_result(entries, user_id)

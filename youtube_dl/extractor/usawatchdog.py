# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from .common import InfoExtractor


class UsaWatchdogIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?usawatchdog\.com/?$'
    _TEST = {
        'url': 'https://usawatchdog.com/',
        'playlist_mincount': 15,
        'info_dict': {
            'id': 'USA Watchdog',
        }}

    def _real_extract(self, url):
        matches = []
        for mobj in re.finditer(r'front-view-title[^<]+<a.+href=["\'](?P<href>https?:(?:www\.)?//usawatchdog.com/[^/]+\/?)[^>]+>(?P<title>[^<]+)',
                                self._download_webpage(url, 'Site Root')):
            matches.append(self.url_result(mobj.group('href'),
                                           video_title=mobj.group('title').encode('utf8')))

        return self.playlist_result(matches, 'USA Watchdog')

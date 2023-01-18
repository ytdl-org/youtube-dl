# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from .common import InfoExtractor

from .rumble import rumble_embedded_id


class UsaWatchdogStoryIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?usawatchdog\.com/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://usawatchdog.com/cv-19-vaccine-warning-cv-19-cure-must-watch-videos/',
        'md5': 'bf40e20aebca9016ca195534028cbb6f',
        'info_dict': {
            'id': 'vcl8gx',
            'ext': 'mp4',
            'timestamp': 1617141926,
            'upload_date': '20210330',
            'title': u'Vaccine Warning \u2013 CV-19 Cure Must Watch Videos',
        }}

    def _real_extract(self, url):
        title = self._match_id(url)
        embeds = rumble_embedded_id(self._download_webpage(url, title))
        return embeds[0] if embeds is not None else None


class UsaWatchdogIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?usawatchdog\.com/$'
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
                           'UsaWatchdogStory', None,
                           mobj.group('title').encode('utf8')))

        return self.playlist_result(matches, 'USA Watchdog')

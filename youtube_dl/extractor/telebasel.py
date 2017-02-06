# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .simplex import SimplexIE
from ..utils import (
    ExtractorError,
    str_or_none,
    strip_or_none,
    remove_end,
    try_get,
    urljoin,
)


class TelebaselBaseIE(InfoExtractor):
    _SERVER_URL = 'https://video.telebasel.ch/'
    _CUSTOMER_ID = '4062'
    _AUTHOR_ID = '4063'


class TelebaselMediathekIE(TelebaselBaseIE):
    IE_DESC = 'telebasel.ch Mediathek'
    _VALID_URL = r'''(?x)
                https?://
                    (?:www\.)?
                    telebasel\.ch/
                    (?!telebasel-archiv)
                    (?!\d+)
                    (?P<show_name>[^/]+)
                    (?:
                        /.*pid=(?P<pid>\d+).*
                    )?
                '''

    _TESTS = [{
        'url': 'https://telebasel.ch/telebasel-gastro-tipp/?aid=4063&pid=75290&channel=15881',
        'only_matching': True,
    }, {
        'url': 'https://telebasel.ch/telebasel-reihe-8',
        'only_matching': True,
    }, {
        'url': 'https://telebasel.ch/telebasel-talk/?channel=15881',
        'only_matching': True,
    }]

    def _extract_video_id(self, url, show_name):
        webpage = self._download_webpage(url, show_name)
        channel_id = self._html_search_regex(
            r'<div[^>]+class=["\']tb-mediathek-videos["\'][^>]+data-channels=["\'](\d+)["\']',
            webpage, 'channel id')

        episodes_url = urljoin(
            self._SERVER_URL,
            'multichannel/%s/%s/.ofdd/json' % (self._CUSTOMER_ID, channel_id))
        episodes = self._download_json(
            episodes_url,
            channel_id,
            note='Downloading episodes JSON',
            errnote='Unable to download episodes JSON',
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        video_id = str_or_none(
            try_get(episodes, lambda x: x['projects'][0]['projectId'], int))
        if not video_id:
            raise ExtractorError('Could not extract video id from the webpage.')

        return video_id

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_name = mobj.group('show_name')
        video_id = mobj.group('pid')

        if not video_id:
            video_id = self._extract_video_id(url, show_name)

        return self.url_result(
            'simplex:%s:%s:%s:%s' % (
                self._SERVER_URL, self._CUSTOMER_ID,
                self._AUTHOR_ID, video_id),
            ie=SimplexIE.ie_key())


class TelebaselArticleIE(TelebaselBaseIE):
    IE_DESC = 'telebasel.ch articles'
    _VALID_URL = r'https?://(?:www\.)?telebasel\.ch/(?P<id>\d{4}/\d{2}/\d{2}/[^/]+)/?'

    _TEST = {
        'url': 'https://telebasel.ch/2017/02/01/report-usr-iii-einfach-erklaert/?channel=105100',
        'info_dict': {
            'id': '2017/02/01/report-usr-iii-einfach-erklaert',
            'title': 'Report: USR III einfach erklärt',
            'description': 'md5:2cb2b94ac023a6a9517cffc58d500c7e',
        },
        'playlist_count': 3,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        search_url = urljoin(
            self._SERVER_URL,
            r'content/%s/%s/(?P<pid>\d+)' % (self._CUSTOMER_ID, self._AUTHOR_ID))
        embed_regex = r'<iframe[^>]+src=["\']%s.+["\']' % search_url
        entries = [
            self.url_result(
                'simplex:%s:%s:%s:%s' % (
                    self._SERVER_URL, self._CUSTOMER_ID,
                    self._AUTHOR_ID, m.group('pid')),
                ie=SimplexIE.ie_key())
            for m in re.finditer(embed_regex, webpage)]

        title = strip_or_none(
            remove_end(self._og_search_title(webpage), '- Telebasel'))
        description = self._og_search_description(webpage)

        return self.playlist_result(
            entries,
            playlist_id=display_id,
            playlist_title=title,
            playlist_description=description)

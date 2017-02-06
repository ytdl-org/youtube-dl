# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .simplex import SimplexIE
from ..utils import (
    ExtractorError,
    str_or_none,
    try_get,
    urljoin,
)


class TelebaselIE(InfoExtractor):
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
    _SERVER_URL = 'https://video.telebasel.ch/'
    _CUSTOMER_ID = '4062'
    _AUTHOR_ID = '4063'

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

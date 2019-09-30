from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ABCClassicFMIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/?(www.)abc.net.au\/classic\/programs\/(?P<show_id>.*)\/(?P<episode>.*)\/(?P<episode_id>.*)'
    _TEST = {
        'url': 'https://www.abc.net.au/classic/programs/mornings/mornings/11536178',
        'md5': '1d7151b404e514f622987b01e90d3c26',
        'info_dict': {
            'id': '11536178',
            'ext': 'mp4',
            'title': 'Mornings',
            'thumbnail': r're:^https?://.*\.jpg'
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        episode_id = mobj.group('episode_id')

        webpage = self._download_webpage(url, episode_id)

        title = self._search_regex(
            r'<meta.*name="title".*content="(?P<value>.*)".*\/>', webpage,
            'title', group='value')

        m3u8_url = self._search_regex(
            r'(["\'])(?P<url>(?:(?!\1).)+\.m3u8(?:(?!\1).)*)\1', webpage,
            'm3u8 url', group='url')

        formats = self._extract_m3u8_formats(
            m3u8_url, episode_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r'<meta.*property="og:image".*content="(?P<url>.*)".*\/>', webpage, 'thumbnail',
            default=False, group='url')

        return {
            'id': episode_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

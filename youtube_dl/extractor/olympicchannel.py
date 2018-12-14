# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class OlympicChannelIE(InfoExtractor):
    IE_NAME = 'olympicchannel'
    _VALID_URL = r'https?://(?:www\.)?olympicchannel\.com/(?P<language>..)/video/detail/(?P<display_id>.+)/?'
    _TEST = {
        'url': 'https://www.olympicchannel.com/en/video/detail/news-of-the-week-with-ash-tulloch-x9414/',
        'md5': 'aee7e665ad4bf45936e0f5d861e56ac5',
        'info_dict': {
            '_type': 'video',
            'id': 'E18112220',
            'ext': 'm3u8',
            'title': 'News of the Week with Ash Tulloch',
            'thumbnail': 'https://img.olympicchannel.com/images/image/private/t_social_share_thumb/primary/fzcmi2e6kji6cnjjs1xz',
            'description': 'Exclusive interviews with Rika Kihira after her Grand Prix finals win, Yuzuru Hanyu&#39;s coach on the injured star, and Valerie Adams on Tokyo.',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)  # video id isn't included in URL, but is in the URL to the video
        display_id = mobj.group('display_id')  # display id is in URL, however
        webpage = self._download_webpage(url, display_id)
        m3u8_url = self._html_search_regex(r'<meta name="video_url" content="(.+?)" />', webpage, 'm3u8_url')  # extract URL of video's m3u8 playlist
        title = self._html_search_regex(r'<meta name="episode_title" content="(.+?)" />', webpage, 'title') or self._html_search_regex(r'<title>(.+?) \| Olympic Channel</title>', webpage, 'title')  # extract title
        video_id = self._search_regex(r'St1-_(.+)_', m3u8_url, 'id')  # extract unique video id from m3u8
        thumbnail_url = self._html_search_regex(r'<meta name="og:image" content="(.+?)" />', webpage, 'thumbnail')
        return {
            '_type': 'video',
            'display_id': display_id,
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'formats': self._extract_m3u8_formats(m3u8_url, video_id),
            'thumbnail': thumbnail_url,
        }

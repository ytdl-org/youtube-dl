from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    get_meta_content,
)


class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/recorded/(?P<videoID>\d+)'
    IE_NAME = 'ustream'
    _TEST = {
        'url': 'http://www.ustream.tv/recorded/20274954',
        'file': '20274954.flv',
        'md5': '088f151799e8f572f84eb62f17d73e5c',
        'info_dict': {
            "uploader": "Young Americans for Liberty",
            "title": "Young Americans for Liberty February 7, 2012 2:28 AM",
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = 'http://tcdn.ustream.tv/video/%s' % video_id
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'data-title="(?P<title>.+)"',
            webpage, 'title')

        uploader = self._html_search_regex(r'data-content-type="channel".*?>(?P<uploader>.*?)</a>',
            webpage, 'uploader', fatal=False, flags=re.DOTALL)

        thumbnail = self._html_search_regex(r'<link rel="image_src" href="(?P<thumb>.*?)"',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': video_title,
            'uploader': uploader,
            'thumbnail': thumbnail,
        }


class UstreamChannelIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/channel/(?P<slug>.+)'
    IE_NAME = 'ustream:channel'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        slug = m.group('slug')
        webpage = self._download_webpage(url, slug)
        channel_id = get_meta_content('ustream:channel_id', webpage)

        BASE = 'http://www.ustream.tv'
        next_url = '/ajax/socialstream/videos/%s/1.json' % channel_id
        video_ids = []
        while next_url:
            reply = json.loads(self._download_webpage(compat_urlparse.urljoin(BASE, next_url), channel_id))
            video_ids.extend(re.findall(r'data-content-id="(\d.*)"', reply['data']))
            next_url = reply['nextUrl']

        urls = ['http://www.ustream.tv/recorded/' + vid for vid in video_ids]
        url_entries = [self.url_result(eurl, 'Ustream') for eurl in urls]
        return self.playlist_result(url_entries, channel_id)

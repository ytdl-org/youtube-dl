from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
)


class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/(?P<type>recorded|embed|embed/recorded)/(?P<videoID>\d+)'
    IE_NAME = 'ustream'
    _TEST = {
        'url': 'http://www.ustream.tv/recorded/20274954',
        'md5': '088f151799e8f572f84eb62f17d73e5c',
        'info_dict': {
            'id': '20274954',
            'ext': 'flv',
            'uploader': 'Young Americans for Liberty',
            'title': 'Young Americans for Liberty February 7, 2012 2:28 AM',
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        # some sites use this embed format (see: http://github.com/rg3/youtube-dl/issues/2990)
        if m.group('type') == 'embed/recorded':
            video_id = m.group('videoID')
            desktop_url = 'http://www.ustream.tv/recorded/' + video_id
            return self.url_result(desktop_url, 'Ustream')
        if m.group('type') == 'embed':
            video_id = m.group('videoID')
            webpage = self._download_webpage(url, video_id)
            desktop_video_id = self._html_search_regex(
                r'ContentVideoIds=\["([^"]*?)"\]', webpage, 'desktop_video_id')
            desktop_url = 'http://www.ustream.tv/recorded/' + desktop_video_id
            return self.url_result(desktop_url, 'Ustream')

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
    _TEST = {
        'url': 'http://www.ustream.tv/channel/channeljapan',
        'info_dict': {
            'id': '10874166',
        },
        'playlist_mincount': 17,
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        display_id = m.group('slug')
        webpage = self._download_webpage(url, display_id)
        channel_id = self._html_search_meta('ustream:channel_id', webpage)

        BASE = 'http://www.ustream.tv'
        next_url = '/ajax/socialstream/videos/%s/1.json' % channel_id
        video_ids = []
        while next_url:
            reply = self._download_json(
                compat_urlparse.urljoin(BASE, next_url), display_id,
                note='Downloading video information (next: %d)' % (len(video_ids) + 1))
            video_ids.extend(re.findall(r'data-content-id="(\d.*)"', reply['data']))
            next_url = reply['nextUrl']

        entries = [
            self.url_result('http://www.ustream.tv/recorded/' + vid, 'Ustream')
            for vid in video_ids]
        return {
            '_type': 'playlist',
            'id': channel_id,
            'display_id': display_id,
            'entries': entries,
        }

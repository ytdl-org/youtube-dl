from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import ExtractorError


class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/(?P<type>recorded|embed|embed/recorded)/(?P<videoID>\d+)'
    IE_NAME = 'ustream'
    _TESTS = [{
        'url': 'http://www.ustream.tv/recorded/20274954',
        'md5': '088f151799e8f572f84eb62f17d73e5c',
        'info_dict': {
            'id': '20274954',
            'ext': 'flv',
            'uploader': 'Young Americans for Liberty',
            'title': 'Young Americans for Liberty February 7, 2012 2:28 AM',
        },
    }, {
        # From http://sportscanada.tv/canadagames/index.php/week2/figure-skating/444
        # Title and uploader available only from params JSON
        'url': 'http://www.ustream.tv/embed/recorded/59307601?ub=ff0000&lc=ff0000&oc=ffffff&uc=ffffff&v=3&wmode=direct',
        'md5': '5a2abf40babeac9812ed20ae12d34e10',
        'info_dict': {
            'id': '59307601',
            'ext': 'flv',
            'title': '-CG11- Canada Games Figure Skating',
            'uploader': 'sportscanadatv',
        }
    }]

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

        params = self._download_json(
            'http://cdngw.ustream.tv/rgwjson/Viewer.getVideo/' + json.dumps({
                'brandId': 1,
                'videoId': int(video_id),
                'autoplay': False,
            }), video_id)

        if 'error' in params:
            raise ExtractorError(params['error']['message'], expected=True)

        video_url = params['flv']

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'data-title="(?P<title>.+)"',
                                              webpage, 'title', default=None)

        if not video_title:
            try:
                video_title = params['moduleConfig']['meta']['title']
            except KeyError:
                pass

        if not video_title:
            video_title = 'Ustream video ' + video_id

        uploader = self._html_search_regex(r'data-content-type="channel".*?>(?P<uploader>.*?)</a>',
                                           webpage, 'uploader', fatal=False, flags=re.DOTALL, default=None)

        if not uploader:
            try:
                uploader = params['moduleConfig']['meta']['userName']
            except KeyError:
                uploader = None

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

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VolAtIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vol\.at/[^?#]*?/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.vol.at/blue-man-group/5593454',
        'md5': '0e4b19b0467a3af136e63cd2fa6cbfde',
        'info_dict': {
            'id': '5593454',
            'ext': 'mp4',
            'title': '"Blau ist mysteriös": Die Blue Man Group im Interview',
        }
    }, {
        'url': 'http://www.vol.at/umbenennung-lustenauer-reichshofstadion-das-sagen-die-lustenauer/5678401',
        'md5': '2e256451e94d661e0eca9af9f3349460',
        'info_dict': {
            'id': '5678401',
            'ext': 'mp4',
            'title': 'Umbenennung Lustenauer Reichshofstadion: Das sagen die Lustenauer!',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)

        video_url_embedded = self._html_search_regex(r'iframe\s*class\s*="vodl-video__iframe"\s*src=\s*"([^"]+)"', webpage, 'videoInfo', fatal=True)
        webpage_embedded = self._download_webpage(video_url_embedded, video_id)
        video_url = self._search_regex(
            r'(?s)file:\s*"([^"]+?(?=\.mp4)\.mp4)[^"]+"',
            webpage_embedded, 'url')
        return {
            'id': video_id,
            'title': title,
            'url': video_url
        }

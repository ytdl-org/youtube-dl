from __future__ import unicode_literals

from .common import InfoExtractor


class EroProfileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eroprofile\.com/m/videos/view/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.eroprofile.com/m/videos/view/sexy-babe-softcore',
        'md5': 'c26f351332edf23e1ea28ce9ec9de32f',
        'info_dict': {
            'id': '3733775',
            'display_id': 'sexy-babe-softcore',
            'ext': 'm4v',
            'title': 'sexy babe softcore',
            'thumbnail': 're:https?://.*\.jpg',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            [r"glbUpdViews\s*\('\d*','(\d+)'", r'p/report/video/(\d+)'],
            webpage, 'video id', default=None)

        video_url = self._search_regex(
            r'<source src="([^"]+)', webpage, 'video url')
        title = self._html_search_regex(
            r'Title:</th><td>([^<]+)</td>', webpage, 'title')
        thumbnail = self._search_regex(
            r'onclick="showVideoPlayer\(\)"><img src="([^"]+)',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'age_limit': 18,
        }

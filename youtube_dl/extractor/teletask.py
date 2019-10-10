from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class TeleTaskIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tele-task\.de/(archive|lecture)/video/(html5/)?(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.tele-task.de/archive/video/html5/26168/',
        'info_dict': {
            'id': '26168',
            'title': 'Duplicate Detection',
        },
        'playlist': [{
            'md5': 'bc7b130ebb52acca59dfb7d96570dee3',
            'info_dict': {
                'id': '26168-speaker',
                'ext': 'mp4',
                'title': 'Duplicate Detection',
                'upload_date': '20141218',
            }
        }, {
            'md5': '22a2da392d2e6a257230cf578df4aed4',
            'info_dict': {
                'id': '26168-slides',
                'ext': 'mp4',
                'title': 'Duplicate Detection',
                'upload_date': '20141218',
            }
        }]
    }

    def _real_extract(self, url):
        lecture_id = self._match_id(url)
        webpage = self._download_webpage(url, lecture_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title')
        upload_date = unified_strdate(self._html_search_regex(
            r'Date:</td><td>([^<]+)</td>', webpage, 'date', fatal=False))

        video_url = self._html_search_regex(r'(https(?:(?!https).)*?(?:hls/video\.m3u8))', webpage, 'video_url')
        video_formats = self._extract_m3u8_formats(
            video_url, lecture_id, 'mp4', fatal=False)

        desktop_url = video_url.replace('video', 'desktop')
        desktop_formats = self._extract_m3u8_formats(desktop_url, lecture_id, 'mp4', fatal=False)

        entries = []
        entries.append({
            'id': '%s-speaker' % (lecture_id),
            'url': video_url,
            'title': title,
            'upload_date': upload_date,
            'formats': video_formats
        })

        entries.append({
            'id': '%s-slides' % (lecture_id),
            'url': desktop_url,
            'title': title,
            'upload_date': upload_date,
            'formats': desktop_formats
        })

        return self.playlist_result(entries, lecture_id, title)

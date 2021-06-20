from __future__ import unicode_literals

from .common import InfoExtractor


class CGTNIE(InfoExtractor):
    _VALID_URL = r'https?://news\.cgtn\.com/news/[0-9]{4}-[0-9]{2}-[0-9]{2}/[a-zA-Z0-9-]+-(?P<id>[a-zA-Z0-9-]+)/index\.html'
    _TESTS = [
        {
            'url': 'https://news.cgtn.com/news/2021-03-09/Up-and-Out-of-Poverty-Ep-1-A-solemn-promise-YuOUaOzGQU/index.html',
            'info_dict': {
                'id': 'YuOUaOzGQU',
                'ext': 'mp4',
                'title': 'Up and Out of Poverty Ep. 1: A solemn promise',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        },
        {
            'url': 'https://news.cgtn.com/news/2021-06-06/China-Indonesia-vow-to-further-deepen-maritime-cooperation-10REvJCewCY/index.html',
            'info_dict': {
                'id': '10REvJCewCY',
                'ext': 'mp4',
                'title': 'China, Indonesia vow to further deepen maritime cooperation',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<div class="news-title">(.+?)</div>', webpage, 'title')
        download_url = self._html_search_regex(r'data-video ="(?P<url>.+m3u8)"', webpage, 'download_url')
        thumbnail = self._html_search_regex(r'<div class="cg-player-container J_player_container" .*? data-poster="(?P<thumbnail>.+jpg)" (.*?)>', webpage, 'thumbnail', fatal=False)

        formats = self._extract_m3u8_formats(
            download_url, video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats
        }

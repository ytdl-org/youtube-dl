from __future__ import unicode_literals
from .common import InfoExtractor


class HellPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hellporno\.com/videos/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://hellporno.com/videos/dixie-is-posing-with-naked-ass-very-erotic/',
        'md5': '1fee339c610d2049699ef2aa699439f1',
        'info_dict': {
            'id': '149116',
            'display_id': 'dixie-is-posing-with-naked-ass-very-erotic',
            'ext': 'mp4',
            'title': 'Dixie is posing with naked ass very erotic',
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'video_id:\s*\'([^\']+)\'', webpage, 'id')

        ext = self._html_search_regex(
            r'postfix:\s*\'([^\']+)\'', webpage, 'ext')[1:]

        video_url = self._html_search_regex(
            r'video_url:\s*\'([^\']+)\'', webpage, 'video_url')

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*Hell Porno</title>', webpage, 'title')

        thumbnail = self._html_search_regex(
            r'preview_url:\s*\'([^\']+)\'',
            webpage, 'thumbnail', fatal=False)

        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'ext': ext,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': 18,
        }

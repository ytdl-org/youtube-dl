from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://beeg.com/5416503',
        'md5': '1bff67111adb785c51d1b42959ec10e5',
        'info_dict': {
            'id': '5416503',
            'ext': 'mp4',
            'title': 'Sultry Striptease',
            'description': 'md5:6db3c6177972822aaba18652ff59c773',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        quality_arr = self._search_regex(
            r'(?s)var\s+qualityArr\s*=\s*{\s*(.+?)\s*}', webpage, 'quality formats')

        formats = [{
            'url': fmt[1],
            'format_id': fmt[0],
            'height': int(fmt[0][:-1]),
        } for fmt in re.findall(r"'([^']+)'\s*:\s*'([^']+)'", quality_arr)]

        self._sort_formats(formats)

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*beeg\.?</title>', webpage, 'title')

        description = self._html_search_regex(
            r'<meta name="description" content="([^"]*)"',
            webpage, 'description', fatal=False)
        thumbnail = self._html_search_regex(
            r'\'previewer.url\'\s*:\s*"([^"]*)"',
            webpage, 'thumbnail', fatal=False)

        categories_str = self._html_search_regex(
            r'<meta name="keywords" content="([^"]+)"', webpage, 'categories', fatal=False)
        categories = (
            None if categories_str is None
            else categories_str.split(','))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'formats': formats,
            'age_limit': 18,
        }

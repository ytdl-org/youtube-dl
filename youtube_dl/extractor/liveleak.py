from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'^(?:http://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    _TESTS = [{
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'file': '757_1364311680.mp4',
        'md5': '0813c2430bea7a46bf13acf3406992f4',
        'info_dict': {
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident'
        }
    },
    {
        'url': 'http://www.liveleak.com/view?i=f93_1390833151',
        'file': 'f93_1390833151.mp4',
        'md5': 'd3f1367d14cc3c15bf24fbfbe04b9abf',
        'info_dict': {
            'description': 'German Television Channel NDR does an exclusive interview with Edward Snowden.\r\nUploaded on LiveLeak cause German Television thinks the rest of the world isn\'t intereseted in Edward Snowden.',
            'uploader': 'ARD_Stinkt',
            'title': 'German Television does first Edward Snowden Interview (ENGLISH)',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)
        sources_raw = self._search_regex(
            r'(?s)sources:\s*(\[.*?\]),', webpage, 'video URLs', default=None)
        if sources_raw is None:
            sources_raw = '[{ %s}]' % (
                self._search_regex(r'(file: ".*?"),', webpage, 'video URL'))

        sources_json = re.sub(r'\s([a-z]+):\s', r'"\1": ', sources_raw)
        sources = json.loads(sources_json)

        formats = [{
            'format_note': s.get('label'),
            'url': s['file'],
        } for s in sources]
        self._sort_formats(formats)

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()
        video_description = self._og_search_description(webpage)
        video_uploader = self._html_search_regex(
            r'By:.*?(\w+)</a>', webpage, 'uploader', fatal=False)

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader,
            'formats': formats,
        }

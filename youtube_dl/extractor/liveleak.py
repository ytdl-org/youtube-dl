from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import int_or_none


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'^(?:http://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    _TESTS = [{
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'md5': '0813c2430bea7a46bf13acf3406992f4',
        'info_dict': {
            'id': '757_1364311680',
            'ext': 'mp4',
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident'
        }
    }, {
        'url': 'http://www.liveleak.com/view?i=f93_1390833151',
        'md5': 'd3f1367d14cc3c15bf24fbfbe04b9abf',
        'info_dict': {
            'id': 'f93_1390833151',
            'ext': 'mp4',
            'description': 'German Television Channel NDR does an exclusive interview with Edward Snowden.\r\nUploaded on LiveLeak cause German Television thinks the rest of the world isn\'t intereseted in Edward Snowden.',
            'uploader': 'ARD_Stinkt',
            'title': 'German Television does first Edward Snowden Interview (ENGLISH)',
        }
    }, {
        'url': 'http://www.liveleak.com/view?i=4f7_1392687779',
        'md5': '42c6d97d54f1db107958760788c5f48f',
        'info_dict': {
            'id': '4f7_1392687779',
            'ext': 'mp4',
            'description': "The guy with the cigarette seems amazingly nonchalant about the whole thing...  I really hope my friends' reactions would be a bit stronger.\r\n\r\nAction-go to 0:55.",
            'uploader': 'CapObveus',
            'title': 'Man is Fatally Struck by Reckless Car While Packing up a Moving Truck',
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()
        video_description = self._og_search_description(webpage)
        video_uploader = self._html_search_regex(
            r'By:.*?(\w+)</a>', webpage, 'uploader', fatal=False)
        age_limit = int_or_none(self._search_regex(
            r'you confirm that you are ([0-9]+) years and over.',
            webpage, 'age limit', default=None))

        sources_raw = self._search_regex(
            r'(?s)sources:\s*(\[.*?\]),', webpage, 'video URLs', default=None)
        if sources_raw is None:
            alt_source = self._search_regex(
                r'(file: ".*?"),', webpage, 'video URL', default=None)
            if alt_source:
                sources_raw = '[{ %s}]' % alt_source
            else:
                # Maybe an embed?
                embed_url = self._search_regex(
                    r'<iframe[^>]+src="(http://www.prochan.com/embed\?[^"]+)"',
                    webpage, 'embed URL')
                return {
                    '_type': 'url_transparent',
                    'url': embed_url,
                    'id': video_id,
                    'title': video_title,
                    'description': video_description,
                    'uploader': video_uploader,
                    'age_limit': age_limit,
                }

        sources_json = re.sub(r'\s([a-z]+):\s', r'"\1": ', sources_raw)
        sources = json.loads(sources_json)

        formats = [{
            'format_note': s.get('label'),
            'url': s['file'],
        } for s in sources]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader,
            'formats': formats,
            'age_limit': age_limit,
        }

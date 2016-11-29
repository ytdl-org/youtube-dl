from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import int_or_none


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<id>[\w_]+)(?:.*)'
    _TESTS = [{
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'md5': '50f79e05ba149149c1b4ea961223d5b3',
        'info_dict': {
            'id': '757_1364311680',
            'ext': 'flv',
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident',
            'thumbnail': 're:^https?://.*\.jpg$'
        }
    }, {
        'url': 'http://www.liveleak.com/view?i=f93_1390833151',
        'md5': 'b13a29626183c9d33944e6a04f41aafc',
        'info_dict': {
            'id': 'f93_1390833151',
            'ext': 'mp4',
            'description': 'German Television Channel NDR does an exclusive interview with Edward Snowden.\r\nUploaded on LiveLeak cause German Television thinks the rest of the world isn\'t intereseted in Edward Snowden.',
            'uploader': 'ARD_Stinkt',
            'title': 'German Television does first Edward Snowden Interview (ENGLISH)',
            'thumbnail': 're:^https?://.*\.jpg$'
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
    }, {
        # Covers https://github.com/rg3/youtube-dl/pull/5983
        'url': 'http://www.liveleak.com/view?i=801_1409392012',
        'md5': '0b3bec2d888c20728ca2ad3642f0ef15',
        'info_dict': {
            'id': '801_1409392012',
            'ext': 'mp4',
            'description': 'Happened on 27.7.2014. \r\nAt 0:53 you can see people still swimming at near beach.',
            'uploader': 'bony333',
            'title': 'Crazy Hungarian tourist films close call waterspout in Croatia',
            'thumbnail': 're:^https?://.*\.jpg$'
        }
    }, {
        # Covers https://github.com/rg3/youtube-dl/pull/10664#issuecomment-247439521
        'url': 'http://m.liveleak.com/view?i=763_1473349649',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': '763_1473349649',
            'ext': 'mp4',
            'title': 'Reporters and public officials ignore epidemic of black on asian violence in Sacramento | Colin Flaherty',
            'description': 'Colin being the warrior he is and showing the injustice Asians in Sacramento are being subjected to.',
            'uploader': 'Ziz',
            'upload_date': '20160908',
            'uploader_id': 'UCEbta5E_jqlZmEJsriTEtnw'
        },
        'params': {
            'skip_download': True,
        },
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:\w+\.)?liveleak\.com/ll_embed\?(?:.*?)i=(?P<id>[\w_]+)(?:.*)',
            webpage)
        if mobj:
            return 'http://www.liveleak.com/view?i=%s' % mobj.group('id')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()
        video_description = self._og_search_description(webpage)
        video_uploader = self._html_search_regex(
            r'By:.*?(\w+)</a>', webpage, 'uploader', fatal=False)
        age_limit = int_or_none(self._search_regex(
            r'you confirm that you are ([0-9]+) years and over.',
            webpage, 'age limit', default=None))
        video_thumbnail = self._og_search_thumbnail(webpage)

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
                    r'<iframe[^>]+src="(https?://(?:www\.)?(?:prochan|youtube)\.com/embed[^"]+)"',
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
            'format_id': '%s' % i,
            'format_note': s.get('label'),
            'url': s['file'],
        } for i, s in enumerate(sources)]

        for i, s in enumerate(sources):
            # Removing '.h264_*.mp4' gives the raw video, which is essentially
            # the same video without the LiveLeak logo at the top (see
            # https://github.com/rg3/youtube-dl/pull/4768)
            orig_url = re.sub(r'\.h264_.+?\.mp4', '', s['file'])
            if s['file'] != orig_url:
                formats.append({
                    'format_id': 'original-%s' % i,
                    'format_note': s.get('label'),
                    'url': orig_url,
                    'preference': 1,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader,
            'formats': formats,
            'age_limit': age_limit,
            'thumbnail': video_thumbnail,
        }

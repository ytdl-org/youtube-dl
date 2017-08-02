from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<id>[\w_]+)(?:.*)'
    _TESTS = [{
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'md5': '0813c2430bea7a46bf13acf3406992f4',
        'info_dict': {
            'id': '757_1364311680',
            'ext': 'mp4',
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident',
            'thumbnail': r're:^https?://.*\.jpg$'
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
            'thumbnail': r're:^https?://.*\.jpg$'
        }
    }, {
        # Prochan embed
        'url': 'http://www.liveleak.com/view?i=4f7_1392687779',
        'md5': '42c6d97d54f1db107958760788c5f48f',
        'info_dict': {
            'id': '4f7_1392687779',
            'ext': 'mp4',
            'description': "The guy with the cigarette seems amazingly nonchalant about the whole thing...  I really hope my friends' reactions would be a bit stronger.\r\n\r\nAction-go to 0:55.",
            'uploader': 'CapObveus',
            'title': 'Man is Fatally Struck by Reckless Car While Packing up a Moving Truck',
            'age_limit': 18,
        },
        'skip': 'Video is dead',
    }, {
        # Covers https://github.com/rg3/youtube-dl/pull/5983
        # Multiple resolutions
        'url': 'http://www.liveleak.com/view?i=801_1409392012',
        'md5': 'c3a449dbaca5c0d1825caecd52a57d7b',
        'info_dict': {
            'id': '801_1409392012',
            'ext': 'mp4',
            'description': 'Happened on 27.7.2014. \r\nAt 0:53 you can see people still swimming at near beach.',
            'uploader': 'bony333',
            'title': 'Crazy Hungarian tourist films close call waterspout in Croatia',
            'thumbnail': r're:^https?://.*\.jpg$'
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

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries:
            # Maybe an embed?
            embed_url = self._search_regex(
                r'<iframe[^>]+src="((?:https?:)?//(?:www\.)?(?:prochan|youtube)\.com/embed[^"]+)"',
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

        info_dict = entries[0]

        for a_format in info_dict['formats']:
            if not a_format.get('height'):
                a_format['height'] = int_or_none(self._search_regex(
                    r'([0-9]+)p\.mp4', a_format['url'], 'height label',
                    default=None))

        self._sort_formats(info_dict['formats'])

        info_dict.update({
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader,
            'age_limit': age_limit,
            'thumbnail': video_thumbnail,
        })

        return info_dict

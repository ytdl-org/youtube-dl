# coding: utf-8
from __future__ import unicode_literals

import re

from .vimple import SprutoBaseIE


class MyviIE(SprutoBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        myvi\.(?:ru/player|tv)/
                            (?:
                                (?:
                                    embed/html|
                                    flash|
                                    api/Video/Get
                                )/|
                                content/preloader\.swf\?.*\bid=
                            )
                            (?P<id>[\da-zA-Z_-]+)
                    '''
    _TESTS = [{
        'url': 'http://myvi.ru/player/embed/html/oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wObeRTZaCATzucDQIDph8hQU0',
        'md5': '571bbdfba9f9ed229dc6d34cc0f335bf',
        'info_dict': {
            'id': 'f16b2bbd-cde8-481c-a981-7cd48605df43',
            'ext': 'mp4',
            'title': 'хозяин жизни',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 25,
        },
    }, {
        'url': 'http://myvi.ru/player/content/preloader.swf?id=oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wOYf1WFpPfc_bWTKGVf_Zafr0',
        'only_matching': True,
    }, {
        'url': 'http://myvi.ru/player/api/Video/Get/oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wObeRTZaCATzucDQIDph8hQU0',
        'only_matching': True,
    }, {
        'url': 'http://myvi.tv/embed/html/oTGTNWdyz4Zwy_u1nraolwZ1odenTd9WkTnRfIL9y8VOgHYqOHApE575x4_xxS9Vn0?ap=0',
        'only_matching': True,
    }, {
        'url': 'http://myvi.ru/player/flash/ocp2qZrHI-eZnHKQBK4cZV60hslH8LALnk0uBfKsB-Q4WnY26SeGoYPi8HWHxu0O30',
        'only_matching': True,
    }]

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//myvi\.(?:ru/player|tv)/(?:embed/html|flash)/[^"]+)\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        spruto = self._download_json(
            'http://myvi.ru/player/api/Video/Get/%s?sig' % video_id, video_id)['sprutoData']

        return self._extract_spruto(spruto, video_id)

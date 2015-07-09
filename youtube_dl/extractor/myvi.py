# coding: utf-8
from __future__ import unicode_literals

from .vimple import SprutoBaseIE


class MyviEmbedIE(SprutoBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        myvi\.ru/player/
                            (?:
                                (?:
                                    embed/html|
                                    api/Video/Get
                                )/|
                                content/preloader\.swf\?.*\bid=
                            )
                            (?P<id>[\da-zA-Z_]+)
                    '''
    _TESTS = [{
        'url': 'http://myvi.ru/player/embed/html/oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wObeRTZaCATzucDQIDph8hQU0',
        'md5': '571bbdfba9f9ed229dc6d34cc0f335bf',
        'info_dict': {
            'id': 'f16b2bbd-cde8-481c-a981-7cd48605df43',
            'ext': 'mp4',
            'title': 'хозяин жизни',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 25,
        },
    }, {
        'url': 'http://myvi.ru/player/content/preloader.swf?id=oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wOYf1WFpPfc_bWTKGVf_Zafr0',
        'only_matching': True,
    }, {
        'url': 'http://myvi.ru/player/api/Video/Get/oOy4euHA6LVwNNAjhD9_Jq5Ha2Qf0rtVMVFMAZav8wObeRTZaCATzucDQIDph8hQU0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        spruto = self._download_json(
            'http://myvi.ru/player/api/Video/Get/%s?sig' % video_id, video_id)['sprutoData']

        return self._extract_spruto(spruto, video_id)

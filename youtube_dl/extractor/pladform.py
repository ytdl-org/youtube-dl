# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    xpath_text,
    qualities,
)


class PladformIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                out\.pladform\.ru/player|
                                static\.pladform\.ru/player\.swf
                            )
                            \?.*\bvideoid=|
                            video\.pladform\.ru/catalog/video/videoid/
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        # http://muz-tv.ru/kinozal/view/7400/
        'url': 'http://out.pladform.ru/player?pl=24822&videoid=100183293',
        'md5': '61f37b575dd27f1bb2e1854777fe31f4',
        'info_dict': {
            'id': '100183293',
            'ext': 'mp4',
            'title': 'Тайны перевала Дятлова • 1 серия 2 часть',
            'description': 'Документальный сериал-расследование одной из самых жутких тайн ХХ века',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 694,
            'age_limit': 0,
        },
    }, {
        'url': 'http://static.pladform.ru/player.swf?pl=21469&videoid=100183293&vkcid=0',
        'only_matching': True,
    }, {
        'url': 'http://video.pladform.ru/catalog/video/videoid/100183293/vkcid/0',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//out\.pladform\.ru/player\?.+?)\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_xml(
            'http://out.pladform.ru/getVideo?pl=1&videoid=%s' % video_id,
            video_id)

        if video.tag == 'error':
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, video.text),
                expected=True)

        quality = qualities(('ld', 'sd', 'hd'))

        formats = [{
            'url': src.text,
            'format_id': src.get('quality'),
            'quality': quality(src.get('quality')),
        } for src in video.findall('./src')]
        self._sort_formats(formats)

        webpage = self._download_webpage(
            'http://video.pladform.ru/catalog/video/videoid/%s' % video_id,
            video_id)

        title = self._og_search_title(webpage, fatal=False) or xpath_text(
            video, './/title', 'title', fatal=True)
        description = self._search_regex(
            r'</h3>\s*<p>([^<]+)</p>', webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage) or xpath_text(
            video, './/cover', 'cover')

        duration = int_or_none(xpath_text(video, './/time', 'duration'))
        age_limit = int_or_none(xpath_text(video, './/age18', 'age limit'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }

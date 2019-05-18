# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    url_or_none,
)


class YandexVideoIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            yandex\.ru(?:/portal/(?:video|efir))?/?\?.*?stream_id=|
                            frontend\.vh\.yandex\.ru/player/
                        )
                        (?P<id>[\da-f]+)
                    '''
    _TESTS = [{
        'url': 'https://yandex.ru/portal/video?stream_id=4dbb262b4fe5cf15a215de4f34eee34d',
        'md5': '33955d7ae052f15853dc41f35f17581c',
        'info_dict': {
            'id': '4dbb262b4fe5cf15a215de4f34eee34d',
            'ext': 'mp4',
            'title': 'В Нью-Йорке баржи и теплоход оторвались от причала и расплылись по Гудзону',
            'description': '',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 0,
            'duration': 30,
            'age_limit': 18,
        },
    }, {
        'url': 'https://yandex.ru/portal/efir?stream_id=4dbb36ec4e0526d58f9f2dc8f0ecf374&from=morda',
        'only_matching': True,
    }, {
        'url': 'https://yandex.ru/?stream_id=4dbb262b4fe5cf15a215de4f34eee34d',
        'only_matching': True,
    }, {
        'url': 'https://frontend.vh.yandex.ru/player/4dbb262b4fe5cf15a215de4f34eee34d?from=morda',
        'only_matching': True,
    }, {
        # vod-episode, series episode
        'url': 'https://yandex.ru/portal/video?stream_id=45b11db6e4b68797919c93751a938cee',
        'only_matching': True,
    }, {
        # episode, sports
        'url': 'https://yandex.ru/?stream_channel=1538487871&stream_id=4132a07f71fb0396be93d74b3477131d',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        content = self._download_json(
            'https://frontend.vh.yandex.ru/v22/player/%s.json' % video_id,
            video_id, query={
                'stream_options': 'hires',
                'disable_trackings': 1,
            })['content']

        m3u8_url = url_or_none(content.get('content_url')) or url_or_none(
            content['streams'][0]['url'])
        title = content.get('title') or content.get('computed_title')

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)

        description = content.get('description')
        thumbnail = content.get('thumbnail')
        timestamp = (int_or_none(content.get('release_date'))
                     or int_or_none(content.get('release_date_ut'))
                     or int_or_none(content.get('start_time')))
        duration = int_or_none(content.get('duration'))
        series = content.get('program_title')
        age_limit = int_or_none(content.get('restriction_age'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'series': series,
            'age_limit': age_limit,
            'formats': formats,
        }

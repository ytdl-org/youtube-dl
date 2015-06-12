# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
)


class TVCIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?tvc\.ru/.*/show/.*id/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.tvc.ru/channel/brand/id/29/show/episodes/episode_id/39702/',
            'md5': 'aa6fb3cf384e18a0ad3b30ee2898beba',
            'info_dict': {
                'id': '74622',
                'display_id': '39702',
                'ext': 'mp4',
                'title': 'События. "События". Эфир от 22.05.2015 14:30',
                'description': 'md5:ad7aa7db22903f983e687b8a3e98c6dd',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 1122,
            },
        },
        {
            'url': 'http://www.tvc.ru/news/show/id/69944',
            'md5': 'b173128ee7b88b5b06c84e5f7880909f',
            'info_dict': {
                'id': '75399',
                'display_id': '69944',
                'ext': 'mp4',
                'title': 'Эксперты: в столице встал вопрос о максимально безопасных остановках',
                'description': 'md5:f675c8eaf23aab9df542d31773ed6518',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 278,
            },
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_url = self._og_search_video_url(webpage)

        video_id = self._search_regex(
            r'video/iframe/id/(\d+)/', video_url, 'video id')

        video_json_url = 'http://www.tvc.ru/video/json/id/%s' % (video_id)

        video_json = self._download_json(video_json_url, video_id)

        formats = []
        for info in video_json.get('path', {}).get('quality', []):
            format_id = self._search_regex(
                r'cdnvideo/([^-]+)-[^/]+/', info.get('url'), 'format id',
                fatal=False)
            formats.append({
                'format_id': str_or_none(format_id),
                'url': info.get('url'),
                'width': int_or_none(info.get('width')),
                'height': int_or_none(info.get('height')),
                'tbr': int_or_none(info.get('bitrate')),
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': int_or_none(video_json.get('duration')),
            'formats': formats,
        }

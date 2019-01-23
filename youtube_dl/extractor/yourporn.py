from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import urljoin


class YourPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?yourporn\.sexy/post/(?P<id>[^/?#&.]+)'
    _TEST = {
        'url': 'https://yourporn.sexy/post/57ffcb2e1179b.html',
        'md5': '6f8682b6464033d87acaa7a8ff0c092e',
        'info_dict': {
            'id': '57ffcb2e1179b',
            'ext': 'mp4',
            'title': 'md5:c9f43630bd968267672651ba905a7d35',
            'thumbnail': r're:^https?://.*\.jpg$',
            'age_limit': 18
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = urljoin(url, self._parse_json(
            self._search_regex(
                r'data-vnfo=(["\'])(?P<data>{.+?})\1', webpage, 'data info',
                group='data'),
            video_id)[video_id]).replace('/cdn/', '/cdn4/')

        title = (self._search_regex(
            r'<[^>]+\bclass=["\']PostEditTA[^>]+>([^<]+)', webpage, 'title',
            default=None) or self._og_search_description(webpage)).strip()
        if '#' in title:
            title = title[0:title.index('#')].strip()
        thumbnail = self._og_search_thumbnail(webpage)
        durationraw = self._search_regex(r'Video Info -> duration:<b>([0-9:]+)</b>',
                                         webpage, 'duration')
        if len(durationraw.split(":")) == 3:
            duration = int((durationraw.split(":")[0])) * 3600 + \
                       int((durationraw.split(":")[1])) * 60 + int((durationraw.split(":")[2]))
        elif len(durationraw.split(":")) == 2:
            duration = int((durationraw.split(":")[0])) * 60 + int((durationraw.split(":")[1]))
        else:
            duration = int((durationraw.split(":")[1]))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'duration': duration,
            'thumbnail': thumbnail,
            'age_limit': 18
        }

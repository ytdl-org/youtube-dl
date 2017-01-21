# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
)
from ..utils import (
    int_or_none,
    try_get,
    RegexNotFoundError,
)


class PornFlipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornflip\.com/v/(?P<id>[0-9A-Za-z]{11})'
    _TEST = {
        'url': 'https://www.pornflip.com/v/wz7DfNhMmep',
        'md5': '98c46639849145ae1fd77af532a9278c',
        'info_dict': {
            'id': 'wz7DfNhMmep',
            'ext': 'mp4',
            'title': '2 Amateurs swallow make his dream cumshots true',
            'uploader': 'figifoto',
            'thumbnail': r're:^https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        uploader = self._html_search_regex(
            r'<span class="name">\s+<a class="ajax" href=".+>\s+<strong>([^<]+)<', webpage, 'uploader', fatal=False)
        flashvars = compat_parse_qs(self._html_search_regex(
            r'<embed.+?flashvars="([^"]+)"',
            webpage, 'flashvars'))
        title = flashvars['video_vars[title]'][0]
        thumbnail = try_get(flashvars, lambda x: x['video_vars[big_thumb]'][0])
        formats = []
        for k, v in flashvars.items():
            height = self._search_regex(r'video_vars\[video_urls\]\[(\d+).+?\]', k, 'height', default=None)
            if height:
                url = v[0]
                formats.append({
                    'height': int_or_none(height),
                    'url': url
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'age_limit': 18,
        }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    compat_urllib_parse,
    compat_urllib_request,
)


class PromptFileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?promptfile\.com/l/(?P<id>[0-9A-Z\-]+)'
    _TEST = {
        'url': 'http://www.promptfile.com/l/D21B4746E9-F01462F0FF',
        'md5': 'd1451b6302da7215485837aaea882c4c',
        'info_dict': {
            'id': 'D21B4746E9-F01462F0FF',
            'ext': 'mp4',
            'title': 'Birds.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if re.search(r'<div.+id="not_found_msg".+>(?!We are).+</div>[^-]', webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        fields = dict(re.findall(r'''(?x)type="hidden"\s+
            name="(.+?)"\s+
            value="(.*?)"
            ''', webpage))
        post = compat_urllib_parse.urlencode(fields)
        req = compat_urllib_request.Request(url, post)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        webpage = self._download_webpage(
            req, video_id, 'Downloading video page')

        url = self._html_search_regex(r'url:\s*\'([^\']+)\'', webpage, 'URL')
        title = self._html_search_regex(
            r'<span.+title="([^"]+)">', webpage, 'title')
        thumbnail = self._html_search_regex(
            r'<div id="player_overlay">.*button>.*?<img src="([^"]+)"',
            webpage, 'thumbnail', fatal=False, flags=re.DOTALL)

        formats = [{
            'format_id': 'sd',
            'url': url,
            'ext': determine_ext(title),
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

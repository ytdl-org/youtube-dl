# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class PromptFileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?promptfile\.com/l/(?P<id>[0-9A-Z\-]+)'
    _TEST = {
        'url': 'http://www.promptfile.com/l/86D1CE8462-576CAAE416',
        'md5': '2125298091532905922013119cc3d2e9',
        'info_dict': {
            'id': '86D1CE8462-576CAAE416',
            'ext': 'mp4',
            'title': 'oceans.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if re.search(r'<div.+id="not_found_msg".+>(?!We are).+</div>[^-]', webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        chash_pattern = r'\$\("#chash"\)\.val\("(.+)"\+\$\("#chash"\)'
        chash = self._search_regex(chash_pattern, webpage, "chash")
        fields = self._hidden_inputs(webpage)
        k = fields.keys()[0]
        fields[k] = chash + fields[k]

        post = urlencode_postdata(fields)
        req = sanitized_Request(url, post)
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

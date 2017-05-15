# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    urlencode_postdata,
)


class PromptFileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?promptfile\.com/l/(?P<id>[0-9A-Z\-]+)'
    _TEST = {
        'url': 'http://www.promptfile.com/l/86D1CE8462-576CAAE416',
        'md5': '5a7e285a26e0d66d9a263fae91bc92ce',
        'info_dict': {
            'id': '86D1CE8462-576CAAE416',
            'ext': 'mp4',
            'title': 'oceans.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if re.search(r'<div.+id="not_found_msg".+>(?!We are).+</div>[^-]', webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        chash = self._search_regex(
            r'val\("([^"]*)"\s*\+\s*\$\("#chash"\)', webpage, 'chash')
        fields = self._hidden_inputs(webpage)
        keys = list(fields.keys())
        chash_key = keys[0] if len(keys) == 1 else next(
            key for key in keys if key.startswith('cha'))
        fields[chash_key] = chash + fields[chash_key]

        webpage = self._download_webpage(
            url, video_id, 'Downloading video page',
            data=urlencode_postdata(fields),
            headers={'Content-type': 'application/x-www-form-urlencoded'})

        video_url = self._search_regex(
            (r'<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1[^>]*>\s*Download File',
             r'<a[^>]+href=(["\'])(?P<url>https?://(?:www\.)?promptfile\.com/file/(?:(?!\1).)+)\1'),
            webpage, 'video url', group='url')
        title = self._html_search_regex(
            r'<span.+title="([^"]+)">', webpage, 'title')
        thumbnail = self._html_search_regex(
            r'<div id="player_overlay">.*button>.*?<img src="([^"]+)"',
            webpage, 'thumbnail', fatal=False, flags=re.DOTALL)

        formats = [{
            'format_id': 'sd',
            'url': video_url,
            'ext': determine_ext(title),
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }

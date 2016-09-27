# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class OnDemandKoreaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ondemandkorea\.com/(?P<id>[^/]+)\.html'
    _TEST = {
        'url': 'http://www.ondemandkorea.com/ask-us-anything-e43.html',
        'info_dict': {
            'id': 'ask-us-anything-e43',
            'ext': 'mp4',
            'title': 'Ask Us Anything : E43',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': 'm3u8 download'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, fatal=False)

        if not webpage:
            # Page sometimes returns captcha page with HTTP 403
            raise ExtractorError('Unable to access page. You may have been blocked.', expected=True)

        if 'msg_block_01.png' in webpage:
            raise ExtractorError('This content is not available in your region.', expected=True)
        
        if 'This video is only available to ODK PLUS members.' in webpage:
            raise ExtractorError('This video is only available to ODK PLUS members.', expected=True)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        manifest_url = self._search_regex(r'file:\s"(https?://[\S].+?/manifest\.m3u8)', webpage, 'manifest')
        formats = self._extract_m3u8_formats(manifest_url, video_id, 'mp4', m3u8_id='hls')
        self._sort_formats(formats)

        subs = re.findall(r'file:\s\'(?P<file>[^\']+\.vtt)\',\s+label:\s+\'(?P<lang>[^\']+)\'', webpage)
        subtitles = {}
        for sub in subs:
            subtitles[sub[1]] = [{'url': 'http://www.ondemandkorea.com' + sub[0], 'ext': sub[0][-3:]}]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }

# coding: utf-8
from __future__ import unicode_literals

import re
import os.path

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    url_basename,
    remove_start,
)


class DemocracynowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?democracynow.org/(?P<id>[^\?]*)'
    IE_NAME = 'democracynow'
    _TESTS = [{
        'url': 'http://www.democracynow.org/shows/2015/7/3',
        'md5': 'fbb8fe3d7a56a5e12431ce2f9b2fab0d',
        'info_dict': {
            'id': '2015-0703-001',
            'ext': 'mp4',
            'title': 'July 03, 2015 - Democracy Now!',
            'description': 'A daily independent global news hour with Amy Goodman & Juan González "What to the Slave is 4th of July?": James Earl Jones Reads Frederick Douglass\u2019 Historic Speech : "This Flag Comes Down Today": Bree Newsome Scales SC Capitol Flagpole, Takes Down Confederate Flag : "We Shall Overcome": Remembering Folk Icon, Activist Pete Seeger in His Own Words & Songs',
        },
    }, {
        'url': 'http://www.democracynow.org/2015/7/3/this_flag_comes_down_today_bree',
        'md5': 'fbb8fe3d7a56a5e12431ce2f9b2fab0d',
        'info_dict': {
            'id': '2015-0703-001',
            'ext': 'mp4',
            'title': '"This Flag Comes Down Today": Bree Newsome Scales SC Capitol Flagpole, Takes Down Confederate Flag',
            'description': 'md5:4d2bc4f0d29f5553c2210a4bc7761a21',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        description = self._og_search_description(webpage)

        json_data = self._parse_json(self._search_regex(
            r'<script[^>]+type="text/json"[^>]*>\s*({[^>]+})', webpage, 'json'),
            display_id)
        video_id = None
        formats = []

        default_lang = 'en'

        subtitles = {}

        def add_subtitle_item(lang, info_dict):
            if lang not in subtitles:
                subtitles[lang] = []
            subtitles[lang].append(info_dict)

        # chapter_file are not subtitles
        if 'caption_file' in json_data:
            add_subtitle_item(default_lang, {
                'url': compat_urlparse.urljoin(url, json_data['caption_file']),
            })

        for subtitle_item in json_data.get('captions', []):
            lang = subtitle_item.get('language', '').lower() or default_lang
            add_subtitle_item(lang, {
                'url': compat_urlparse.urljoin(url, subtitle_item['url']),
            })

        for key in ('file', 'audio', 'video'):
            media_url = json_data.get(key, '')
            if not media_url:
                continue
            media_url = re.sub(r'\?.*', '', compat_urlparse.urljoin(url, media_url))
            video_id = video_id or remove_start(os.path.splitext(url_basename(media_url))[0], 'dn')
            formats.append({
                'url': media_url,
            })

        self._sort_formats(formats)

        return {
            'id': video_id or display_id,
            'title': json_data['title'],
            'description': description,
            'subtitles': subtitles,
            'formats': formats,
        }

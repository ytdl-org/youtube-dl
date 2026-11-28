# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
)

class NZOnScreenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nzonscreen\.com/title/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.nzonscreen.com/title/watermark-2001',
        'md5': '9d8885fb0d8aeae80a15e7191e54230a',
        'info_dict': {
            'id': 'watermark-2001',
            'ext': 'm4v',
            'title': 'Watermark',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1 class=\'hero-video__title\'>(.+?)</h1>',
            webpage, 'title')
        main_clip = self._html_search_regex(r'data-video-config=\'(.+?)\'',
            webpage, 'source')
        main_clip = json.loads(main_clip)

        clips = self._html_search_regex(r'<div class=\'grid js_clip_selector (clip-selector)\'',
            webpage, 'clips', default=False)

        if clips:
            clips_list = self._download_json('https://www.nzonscreen.com/html5/video_data/' + video_id,
                video_id)
        else:
            clips_list = [main_clip];

        entries = []
        clip_id = 0

        for clip in clips_list:
            clip_id = len(entries)

            entries.append({
                'id': '%s_part_%d' % (video_id, clip_id+1),
                'title': title,
                'url': url,
                'formats': [],
            })

            for fmt in ["flv", "h264"]:
                for definition in ["lo", "hi", "hd"]:
                    if clip[fmt][definition + "_res_mb"]:
                        entries[clip_id]["formats"].append({
                            'format_id': '%s-%s' % (fmt, definition),
                            'url': clip[fmt][definition + "_res"],
                        })

        if len(entries) == 1:
            info = entries[0]
            info['id'] = video_id
        else:
            info = {
                '_type': 'multi_video',
                'entries': entries,
                'id': video_id,
                'title': title,
            }

        return info
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
        'md5': '7743cb2c319c27357bc75dd8bcde5d11',
        'info_dict': {
            'id': 'watermark-2001',
            'ext': 'm4v',
            'title': 'Watermark',
            'description': 'md5:c654662c3985fb0cef75812fbb378174',
            #'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1 class=\'hero-video__title\'>(.+?)</h1>',
            webpage, 'title')
        main_clip = self._html_search_regex(r'data-video-config=\'(.+?)\'',
            webpage, 'source')
        main_clip = json.loads(main_clip)

        clips = self._html_search_regex(r'<div class=\'grid js_clip_selector (clip-selector)\'',
            webpage, 'clips', 0)

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
                'id': "%s-clip_%d_of_%d" % (video_id, clip_id + 1, len(clips_list)),
                'title': title,
                'description': self._og_search_description(webpage),
                'url': url,
                'formats': [],
            })

            for fmt in ["h264", "flv"]:
                for definition in ["hd", "hi", "lo"]:
                    if clip[fmt][definition + "_res_mb"]:
                        entries[clip_id]["formats"].append({
                            'format_id': '%s-%s' % (fmt, definition),
                            'url': clip[fmt][definition + "_res"],
                        })

        return self.playlist_result(entries, video_id, title, self._og_search_description(webpage))
        return {
            #'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
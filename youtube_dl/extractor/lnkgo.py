# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class LnkGoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lnkgo\.alfa\.lt/visi-video/(?P<show>[^/]+)/ziurek-(?P<id>[A-Za-z0-9-]+)'
    _TESTS = [{
        'url': 'http://lnkgo.alfa.lt/visi-video/yra-kaip-yra/ziurek-yra-kaip-yra-162',
        'info_dict': {
            'id': '46712',
            'ext': 'mp4',
            'title': 'Yra kaip yra',
            'upload_date': '20150107',
            'description': 'md5:d82a5e36b775b7048617f263a0e3475e',
            'age_limit': 7,
            'duration': 3019,
            'thumbnail': r're:^https?://.*\.jpg$'
        },
        'params': {
            'skip_download': True,  # HLS download
        },
    }, {
        'url': 'http://lnkgo.alfa.lt/visi-video/aktualai-pratesimas/ziurek-nerdas-taiso-kompiuteri-2',
        'info_dict': {
            'id': '47289',
            'ext': 'mp4',
            'title': 'Nėrdas: Kompiuterio Valymas',
            'upload_date': '20150113',
            'description': 'md5:7352d113a242a808676ff17e69db6a69',
            'age_limit': 18,
            'duration': 346,
            'thumbnail': r're:^https?://.*\.jpg$'
        },
        'params': {
            'skip_download': True,  # HLS download
        },
    }]
    _AGE_LIMITS = {
        'N-7': 7,
        'N-14': 14,
        'S': 18,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(
            url, display_id, 'Downloading player webpage')

        video_id = self._search_regex(
            r'data-ep="([^"]+)"', webpage, 'video ID')
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        upload_date = unified_strdate(self._search_regex(
            r'class="[^"]*meta-item[^"]*air-time[^"]*">.*?<strong>([^<]+)</strong>', webpage, 'upload date', fatal=False))

        thumbnail_w = int_or_none(
            self._og_search_property('image:width', webpage, 'thumbnail width', fatal=False))
        thumbnail_h = int_or_none(
            self._og_search_property('image:height', webpage, 'thumbnail height', fatal=False))
        thumbnail = {
            'url': self._og_search_thumbnail(webpage),
        }
        if thumbnail_w and thumbnail_h:
            thumbnail.update({
                'width': thumbnail_w,
                'height': thumbnail_h,
            })

        config = self._parse_json(self._search_regex(
            r'episodePlayer\((\{.*?\}),\s*\{', webpage, 'sources'), video_id)

        if config.get('pGeo'):
            self.report_warning(
                'This content might not be available in your country due to copyright reasons')

        formats = [{
            'format_id': 'hls',
            'ext': 'mp4',
            'url': config['EpisodeVideoLink_HLS'],
        }]

        m = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<play_path>.+)$', config['EpisodeVideoLink'])
        if m:
            formats.append({
                'format_id': 'rtmp',
                'ext': 'flv',
                'url': m.group('url'),
                'play_path': m.group('play_path'),
                'page_url': url,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnails': [thumbnail],
            'duration': int_or_none(config.get('VideoTime')),
            'description': description,
            'age_limit': self._AGE_LIMITS.get(config.get('PGRating'), 0),
            'upload_date': upload_date,
        }

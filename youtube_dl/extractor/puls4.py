# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
    int_or_none,
)


class Puls4IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?puls4\.com/video/[^/]+/play/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.puls4.com/video/pro-und-contra/play/2716816',
        'md5': '49f6a6629747eeec43cef6a46b5df81d',
        'info_dict': {
            'id': '2716816',
            'ext': 'mp4',
            'title': 'Pro und Contra vom 23.02.2015',
            'description': 'md5:293e44634d9477a67122489994675db6',
            'duration': 2989,
            'upload_date': '20150224',
            'uploader': 'PULS_4',
        },
        'skip': 'Only works from Germany',
    }, {
        'url': 'http://www.puls4.com/video/kult-spielfilme/play/1298106',
        'md5': '6a48316c8903ece8dab9b9a7bf7a59ec',
        'info_dict': {
            'id': '1298106',
            'ext': 'mp4',
            'title': 'Lucky Fritz',
        },
        'skip': 'Only works from Germany',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        error_message = self._html_search_regex(
            r'<div class="message-error">(.+?)</div>',
            webpage, 'error message', default=None)
        if error_message:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_message), expected=True)

        real_url = self._html_search_regex(
            r'\"fsk-button\".+?href=\"([^"]+)',
            webpage, 'fsk_button', default=None)
        if real_url:
            webpage = self._download_webpage(real_url, video_id)

        player = self._search_regex(
            r'p4_video_player(?:_iframe)?\("video_\d+_container"\s*,(.+?)\);\s*\}',
            webpage, 'player')

        player_json = self._parse_json(
            '[%s]' % player, video_id,
            transform_source=lambda s: s.replace('undefined,', ''))

        formats = None
        result = None

        for v in player_json:
            if isinstance(v, list) and not formats:
                formats = [{
                    'url': f['url'],
                    'format': 'hd' if f.get('hd') else 'sd',
                    'width': int_or_none(f.get('size_x')),
                    'height': int_or_none(f.get('size_y')),
                    'tbr': int_or_none(f.get('bitrate')),
                } for f in v]
                self._sort_formats(formats)
            elif isinstance(v, dict) and not result:
                result = {
                    'id': video_id,
                    'title': v['videopartname'].strip(),
                    'description': v.get('videotitle'),
                    'duration': int_or_none(v.get('videoduration') or v.get('episodeduration')),
                    'upload_date': unified_strdate(v.get('clipreleasetime')),
                    'uploader': v.get('channel'),
                }

        result['formats'] = formats

        return result

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    urlencode_postdata,
)


class HiDiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hidive\.com/stream/(?P<title>[^/]+)/(?P<key>[^/?#&]+)'
    # Using X-Forwarded-For results in 403 HTTP error for HLS fragments,
    # so disabling geo bypass completely
    _GEO_BYPASS = False

    _TESTS = [{
        'url': 'https://www.hidive.com/stream/the-comic-artist-and-his-assistants/s01e001',
        'info_dict': {
            'id': 'the-comic-artist-and-his-assistants/s01e001',
            'ext': 'mp4',
            'title': 'the-comic-artist-and-his-assistants/s01e001',
            'series': 'the-comic-artist-and-his-assistants',
            'season_number': 1,
            'episode_number': 1,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title, key = mobj.group('title', 'key')
        video_id = '%s/%s' % (title, key)

        settings = self._download_json(
            'https://www.hidive.com/play/settings', video_id,
            data=urlencode_postdata({
                'Title': title,
                'Key': key,
            }))

        restriction = settings.get('restrictionReason')
        if restriction == 'RegionRestricted':
            self.raise_geo_restricted()

        if restriction and restriction != 'None':
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, restriction), expected=True)

        formats = []
        subtitles = {}
        for rendition_id, rendition in settings['renditions'].items():
            bitrates = rendition.get('bitrates')
            if not isinstance(bitrates, dict):
                continue
            m3u8_url = bitrates.get('hls')
            if not isinstance(m3u8_url, compat_str):
                continue
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='%s-hls' % rendition_id, fatal=False))
            cc_files = rendition.get('ccFiles')
            if not isinstance(cc_files, list):
                continue
            for cc_file in cc_files:
                if not isinstance(cc_file, list) or len(cc_file) < 3:
                    continue
                cc_lang = cc_file[0]
                cc_url = cc_file[2]
                if not isinstance(cc_lang, compat_str) or not isinstance(
                        cc_url, compat_str):
                    continue
                subtitles.setdefault(cc_lang, []).append({
                    'url': cc_url,
                })

        season_number = int_or_none(self._search_regex(
            r's(\d+)', key, 'season number', default=None))
        episode_number = int_or_none(self._search_regex(
            r'e(\d+)', key, 'episode number', default=None))

        return {
            'id': video_id,
            'title': video_id,
            'subtitles': subtitles,
            'formats': formats,
            'series': title,
            'season_number': season_number,
            'episode_number': episode_number,
        }

# coding: utf-8
from __future__ import unicode_literals

import re
import time

from ..utils import (
    ExtractorError,
    decode_packed_codes,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    float_or_none,
    parse_filesize,
    parse_resolution,
    strip_or_none,
)
from .common import InfoExtractor


class Mp4UploadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mp4upload\.com/(?:embed-)?(?P<id>[a-z\d]+)'
    _TESTS = [{
        'url': 'http://www.mp4upload.com/e52ycvdl4x29',
        'md5': '09780a74b0de79ada5f9a8955f0704fc',
        'info_dict': {
            'id': 'e52ycvdl4x29',
            'ext': 'mp4',
            'title': '橋本潮 - ロマンティックあげるよ.mp4',
            'timestamp': 1467471956,
            'thumbnail': r're:^https?://.*\.jpg$',
            'vcodec': 'ffh264',
            'width': 454,
            'height': 360,
            'fps': 29.970,
            'acodec': 'ffaac',
            'asr': 44100,
            'abr': 96,
            'vbr': 266,
            'upload_date': '20160702',
        },
    }, {
        'url': 'https://www.mp4upload.com/embed-e52ycvdl4x29.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page_url = 'https://www.mp4upload.com/%s' % video_id
        embed_url = 'https://www.mp4upload.com/embed-%s.html' % video_id

        webpage = self._download_webpage(page_url, video_id)
        if 'File not found' in webpage or 'File Not Found' in webpage:
            raise ExtractorError('File not found', expected=True, video_id=video_id)

        title = strip_or_none(get_element_by_class('dfilename', webpage))
        if not title:
            raise ExtractorError('Title not found', expected=True, video_id=video_id)

        try:
            # It contains only `source url` and `thumbnail`
            jw_dict = self._extract_jwplayer_data(
                decode_packed_codes(
                    get_element_by_id(
                        'player',
                        self._download_webpage(embed_url, video_id, note='Downloading embed webpage')
                    )
                ).replace('\\\'', '"'),
                video_id, base_url=embed_url, require_title=False
            )
        except TypeError:
            jw_dict = None
        if not jw_dict:
            raise ExtractorError('I can\'t find player data', video_id=video_id)

        acodec = None
        asr = None
        abr = None
        audio_raw = self._html_search_regex(
            r'<li><span class="infoname">Audio info:</span><span>(.+?)</span></li>',
            webpage, 'audioinfo', fatal=False)
        if audio_raw:
            audmatch = re.search(r'(.+?), (\d+) kbps, (\d+) Hz', audio_raw)
            if audmatch:
                (acodec, abr, asr) = audmatch.groups()

        resolution = {}
        resolution_raw = self._html_search_regex(
            r'<li><span class="infoname">Resolution:</span><span>(.+?)</span></li>',
            webpage, 'resolution', fatal=False)
        if resolution_raw:
            resolution = parse_resolution(resolution_raw)

        vcodec = self._html_search_regex(
            r'<li><span class="infoname">Codec:</span><span>(.+?)</span></li>',
            webpage, 'codec', fatal=False)

        fps = self._html_search_regex(
            r'<li><span class="infoname">Framerate:</span><span>(.+?) fps</span></li>',
            webpage, 'framerate', fatal=False)

        vbr = self._html_search_regex(
            r'<li><span class="infoname">Bitrate:</span><span>(.+?) Kbps</span></li>',
            webpage, 'framerate', fatal=False)

        filesize_approx = parse_filesize(
            self._html_search_regex(
                r'<span class="statd">Size</span>\s+<span>(.+?)</span>',
                webpage, 'filesize', fatal=False
            )
        )

        timestamp = None
        date_raw = self._search_regex(r'Uploaded on(.+?)</div>', webpage, 'timestamp', fatal=False, flags=re.DOTALL)
        if date_raw:
            try:
                timestamp = time.mktime(time.strptime(
                    re.sub(r'[^\d\-\:]+', '', date_raw),
                    '%Y-%m-%d%H:%M:%S'
                ))
            except ValueError:
                pass

        return {
            'title': title,
            'id': video_id,
            'thumbnail': jw_dict.get('thumbnail'),
            'formats': [{
                'url': jw_dict.get('formats', [{}])[0].get('url'),
                'ext': jw_dict.get('formats', [{}])[0].get('ext'),
                'filesize_approx': filesize_approx,
                'vcodec': vcodec,
                'width': resolution.get('width'),
                'height': resolution.get('height'),
                'fps': float_or_none(fps),
                'acodec': acodec,
                'abr': int_or_none(abr),
                'asr': int_or_none(asr),
                'vbr': int_or_none(vbr),
            }],
            'timestamp': timestamp,
        }

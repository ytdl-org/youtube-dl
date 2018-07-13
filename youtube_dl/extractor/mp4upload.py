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

        info_dict = {
            'title': title,
            'id': video_id,
        }

        embedpage = self._download_webpage(embed_url, video_id, note='Downloading embed webpage')

        # It contains only `source url` and `thumbnail`
        poor_info_dict = self._extract_jwplayer_data(
            decode_packed_codes(
                get_element_by_id('player', embedpage)
            ).replace('\\\'', '"'),
            video_id, base_url=embed_url, require_title=False
        )
        if not poor_info_dict:
            raise ExtractorError('I can\'t find player data', video_id=video_id)

        info_dict['thumbnail'] = poor_info_dict.get('thumbnail')
        _f = {
            'url': poor_info_dict.get('formats', [{}])[0].get('url'),
            'ext': poor_info_dict.get('formats', [{}])[0].get('ext'),
            'format_id': '1',
        }

        file_info = re.findall(
            r'>(?P<label>[^<:]+):</span><span>(?P<value>[^<]+)</span></li>',
            get_element_by_class('fileinfo', webpage)
        )
        if file_info:
            for info in file_info:
                if info[0] == 'Codec':
                    _f['vcodec'] = info[1]

                elif info[0] == 'Resolution':
                    _f['resolution'] = info[1].replace(' ', '')
                    resmatch = re.search(r'(?P<width>\d+)\s*x\s*(?P<height>\d+)', info[1])
                    if resmatch:
                        _f['width'] = int(resmatch.group('width'))
                        _f['height'] = int(resmatch.group('height'))

                elif info[0] == 'Framerate':
                    fps = float_or_none(re.sub(r'[^\d\.]+', '', info[1]))
                    if fps < 100:
                        _f['fps'] = fps

                elif info[0] == 'Audio info':
                    audmatch = re.search(r'(?P<acodec>.+?), (?P<abr>\d+) kbps, (?P<asr>\d+) Hz', info[1])
                    if audmatch:
                        _f['acodec'] = audmatch.group('acodec')
                        _f['abr'] = int(audmatch.group('abr'))
                        _f['asr'] = int(audmatch.group('asr'))

                elif info[0] == 'Bitrate':
                    _f['vbr'] = int_or_none(re.sub(r'\D+', '', info[1]))

        _f['filesize_approx'] = parse_filesize(
            self._html_search_regex(
                r'<span class="statd">Size</span>\s+<span>(.+?)</span>',
                webpage, 'filesize', fatal=False
            )
        )
        info_dict['formats'] = [_f]

        date_raw = self._search_regex(r'Uploaded on(.+?)</div>', webpage, 'timestamp', fatal=False, flags=re.DOTALL)
        if date_raw:
            try:
                info_dict['timestamp'] = time.mktime(time.strptime(
                    re.sub(r'[^\d\-\:]+', '', date_raw),
                    '%Y-%m-%d%H:%M:%S'
                ))
            except ValueError:
                pass

        return info_dict

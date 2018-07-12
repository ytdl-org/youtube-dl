# coding: utf-8
from __future__ import unicode_literals

import re
import time

from ..utils import (
    ExtractorError,
    decode_packed_codes,
    get_element_by_class,
    get_element_by_id,
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

            # Something adds this to the _real_extract return value, and the test runner expects it present.
            # Should probably be autocalculated from the timestamp instead, just like _real_extract.
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

        file_info = re.findall(
            r'>(?P<label>[^<:]+):</span><span>(?P<value>[^<]+)</span></li>',
            get_element_by_class('fileinfo', webpage)
        )
        if not file_info:
            raise ExtractorError('I can\'t find file info', video_id=video_id)

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
            'url': poor_info_dict.get('formats')[0].get('url'),
            'ext': poor_info_dict.get('formats')[0].get('ext'),
            'format_id': '1',
        }

        for info in file_info:
            if info[0] == 'Codec':
                _f['vcodec'] = info[1]

            elif info[0] == 'Resolution':
                _f['resolution'] = info[1].replace(' ', '')
                resmatch = re.search(r'(?P<width>[\d]+) x (?P<height>[\d]+)', info[1])
                if resmatch:
                    _f['width'] = int(resmatch.group('width'))
                    _f['height'] = int(resmatch.group('height'))

            elif info[0] == 'Framerate' and info[1] != '1000.000 fps':
                _f['fps'] = float(info[1].replace(' fps', ''))

            elif info[0] == 'Audio info':
                audmatch = re.search(r'(?P<acodec>.+?), (?P<abr>[\d]+) kbps, (?P<asr>[\d]+) Hz', info[1])
                if audmatch:
                    _f['acodec'] = audmatch.group('acodec')
                    _f['abr'] = int(audmatch.group('abr'))
                    _f['asr'] = int(audmatch.group('asr'))

            elif info[0] == 'Bitrate':
                _f['vbr'] = int(info[1].replace(' Kbps', ''))

        _f['filesize_approx'] = parse_filesize(
            self._html_search_regex(
                r'<span class="statd">Size</span>\s+<span>(.+?)</span>',
                webpage, 'filesize', fatal=False
            )
        )
        info_dict['formats'] = [_f]

        # can't use _html_search_regex, there's data both inside and outside a bold tag and I need it all
        date_raw = self._search_regex(r'Uploaded on(.+?)</div>', webpage, 'timestamp', fatal=False, flags=re.DOTALL)
        if date_raw:
            date_raw = re.sub(r'<[^>]+>', '', date_raw)
            date_raw = re.sub(r'[\s]+', ' ', date_raw)
            info_dict['timestamp'] = time.mktime(time.strptime(date_raw, ' %Y-%m-%d %H:%M:%S '))

        return info_dict

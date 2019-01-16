# coding: utf-8
from __future__ import unicode_literals

import json
import os
import re
import subprocess
import tempfile
import dryscrape, sys

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_kwargs,
)
from ..utils import (
    check_executable,
    determine_ext,
    encodeArgument,
    ExtractorError,
    get_element_by_id,
    get_exe_version,
    is_outdated_version,
    std_headers,
)

if 'linux' in sys.platform:
    dryscrape.start_xvfb()

class OpenloadIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?P<host>
                            (?:www\.)?
                            (?:
                                openload\.(?:co|io|link)|
                                oload\.(?:tv|stream|site|xyz|win|download|cloud|cc|icu|fun)
                            )
                        )/
                        (?:f|embed)/
                        (?P<id>[a-zA-Z0-9-_]+)
                    '''

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/rjC09fkPLYs',
        'info_dict': {
            'id': 'rjC09fkPLYs',
            'ext': 'mp4',
            'title': 'movie.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': {
                'en': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,  # test subtitles only
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        'url': 'https://openload.co/f/_-ztPaZtMhM/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/embed/e-Ixz9ZR5L0/ but available
        # via https://openload.co/f/e-Ixz9ZR5L0/
        'url': 'https://openload.co/f/e-Ixz9ZR5L0/',
        'only_matching': True,
    }, {
        'url': 'https://oload.tv/embed/KnG-kKZdcfY/',
        'only_matching': True,
    }, {
        'url': 'http://www.openload.link/f/KnG-kKZdcfY',
        'only_matching': True,
    }, {
        'url': 'https://oload.stream/f/KnG-kKZdcfY',
        'only_matching': True,
    }, {
        'url': 'https://oload.xyz/f/WwRBpzW8Wtk',
        'only_matching': True,
    }, {
        'url': 'https://oload.win/f/kUEfGclsU9o',
        'only_matching': True,
    }, {
        'url': 'https://oload.download/f/kUEfGclsU9o',
        'only_matching': True,
    }, {
        'url': 'https://oload.cloud/f/4ZDnBXRWiB8',
        'only_matching': True,
    }, {
        # Its title has not got its extension but url has it
        'url': 'https://oload.download/f/N4Otkw39VCw/Tomb.Raider.2018.HDRip.XviD.AC3-EVO.avi.mp4',
        'only_matching': True,
    }, {
        'url': 'https://oload.cc/embed/5NEAbI2BDSk',
        'only_matching': True,
    }, {
        'url': 'https://oload.icu/f/-_i4y_F_Hs8',
        'only_matching': True,
    }, {
        'url': 'https://oload.fun/f/gb6G1H4sHXY',
        'only_matching': True,
    }]

    _USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\']((?:https?://)?(?:openload\.(?:co|io)|oload\.tv)/embed/[a-zA-Z0-9-_]+)',
            webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = mobj.group('id')

        url_pattern = 'https://%s/%%s/%s/' % (host, video_id)
        headers = {
            'User-Agent': self._USER_AGENT,
        }

        for path in ('embed', 'f'):
            page_url = url_pattern % path
            last = path == 'f'
            webpage = self._download_webpage(
                page_url, video_id, 'Downloading %s webpage' % path,
                headers=headers, fatal=last)
            if not webpage:
                continue
            if 'File not found' in webpage or 'deleted by the owner' in webpage:
                if not last:
                    continue
                raise ExtractorError('File not found', expected=True, video_id=video_id)
            break

        sess = dryscrape.Session()
        sess.visit(url)
        webpage = sess.body()

        decoded_id = (get_element_by_id('streamurl', webpage) or
                      get_element_by_id('streamuri', webpage) or
                      get_element_by_id('streamurj', webpage) or
                      self._search_regex(
                          (r'>\s*([\w-]+~\d{10,}~\d+\.\d+\.0\.0~[\w-]+)\s*<',
                           r'>\s*([\w~-]+~\d+\.\d+\.\d+\.\d+~[\w~-]+)',
                           r'>\s*([\w-]+~\d{10,}~(?:[a-f\d]+:){2}:~[\w-]+)\s*<',
                           r'>\s*([\w~-]+~[a-f0-9:]+~[\w~-]+)\s*<',
                           r'>\s*([\w~-]+~[a-f0-9:]+~[\w~-]+)'), webpage,
                          'stream URL'))

        video_url = 'https://%s/stream/%s?mime=true' % (host, decoded_id)

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        entries = self._parse_html5_media_entries(page_url, webpage, video_id)
        entry = entries[0] if entries else {}
        subtitles = entry.get('subtitles')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': entry.get('thumbnail') or self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            'ext': determine_ext(title, None) or determine_ext(url, 'mp4'),
            'subtitles': subtitles,
            'http_headers': headers,
        }

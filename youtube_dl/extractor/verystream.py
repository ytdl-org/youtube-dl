# coding: utf-8
from __future__ import unicode_literals

import json
import os
import random
import re
import subprocess
import tempfile

from .openload import PhantomJSwrapper

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

class VerystreamIE(InfoExtractor):
    _DOMAINS = r'(?:verystream\.com)'
    _VALID_URL = r'''(?x)
                    https?://
                        (?P<host>
                            (?:www\.)?
                            %s
                        )/
                        (?:e|stream)/
                        (?P<id>[a-zA-Z0-9-_]+)
                    ''' % _DOMAINS

    _TESTS = [{
        'url': 'https://verystream.com/e/b8NWEgkqNLI/',
        'only_matching': True,
    }]

    _USER_AGENT_TPL = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.{build}.{patch} Safari/537.36'

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\']((?:https?://)?%s/stream/[a-zA-Z0-9-_]+)'
            % VerystreamIE._DOMAINS, webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = mobj.group('id')

        url_pattern = 'https://%s/%%s/%s/' % (host, video_id)
        headers = {
            'User-Agent': self._USER_AGENT_TPL % {
                'major': random.randint(63, 73),
                'build': random.randint(3239, 3683),
                'patch': random.randint(0, 100),
            },
        }

        for path in ('e', 'stream'):
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

        phantom = PhantomJSwrapper(self, required_version='2.0')
        webpage, _ = phantom.get(page_url, html=webpage, video_id=video_id, headers=headers)

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

        video_url = 'https://%s/gettoken/%s?mime=true' % (host, decoded_id)

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

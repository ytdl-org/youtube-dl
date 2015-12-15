# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import binascii
import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
    determine_ext,
)
from ..compat import compat_ord


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<video_id>[0-9]+)?/?(?P<display_id>.*)'
    _TESTS = [
        {
            'url': 'http://teamcoco.com/video/80187/conan-becomes-a-mary-kay-beauty-consultant',
            'md5': '3f7746aa0dc86de18df7539903d399ea',
            'info_dict': {
                'id': '80187',
                'ext': 'mp4',
                'title': 'Conan Becomes A Mary Kay Beauty Consultant',
                'description': 'Mary Kay is perhaps the most trusted name in female beauty, so of course Conan is a natural choice to sell their products.',
                'duration': 504,
                'age_limit': 0,
            }
        }, {
            'url': 'http://teamcoco.com/video/louis-ck-interview-george-w-bush',
            'md5': 'cde9ba0fa3506f5f017ce11ead928f9a',
            'info_dict': {
                'id': '19705',
                'ext': 'mp4',
                'description': 'Louis C.K. got starstruck by George W. Bush, so what? Part one.',
                'title': 'Louis C.K. Interview Pt. 1 11/3/11',
                'duration': 288,
                'age_limit': 0,
            }
        }, {
            'url': 'http://teamcoco.com/video/timothy-olyphant-drinking-whiskey',
            'info_dict': {
                'id': '88748',
                'ext': 'mp4',
                'title': 'Timothy Olyphant Raises A Toast To “Justified”',
                'description': 'md5:15501f23f020e793aeca761205e42c24',
            },
            'params': {
                'skip_download': True,  # m3u8 downloads
            }
        }, {
            'url': 'http://teamcoco.com/video/full-episode-mon-6-1-joel-mchale-jake-tapper-and-musical-guest-courtney-barnett?playlist=x;eyJ0eXBlIjoidGFnIiwiaWQiOjl9',
            'info_dict': {
                'id': '89341',
                'ext': 'mp4',
                'title': 'Full Episode - Mon. 6/1 - Joel McHale, Jake Tapper, And Musical Guest Courtney Barnett',
                'description': 'Guests: Joel McHale, Jake Tapper, And Musical Guest Courtney Barnett',
            },
            'params': {
                'skip_download': True,  # m3u8 downloads
            }
        }
    ]
    _VIDEO_ID_REGEXES = (
        r'"eVar42"\s*:\s*(\d+)',
        r'Ginger\.TeamCoco\.openInApp\("video",\s*"([^"]+)"',
        r'"id_not"\s*:\s*(\d+)'
    )

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        display_id = mobj.group('display_id')
        webpage, urlh = self._download_webpage_handle(url, display_id)
        if 'src=expired' in urlh.geturl():
            raise ExtractorError('This video is expired.', expected=True)

        video_id = mobj.group('video_id')
        if not video_id:
            video_id = self._html_search_regex(
                self._VIDEO_ID_REGEXES, webpage, 'video id')

        data = None

        preload_codes = self._html_search_regex(
            r'(function.+)setTimeout\(function\(\)\{playlist',
            webpage, 'preload codes')
        base64_fragments = re.findall(r'"([a-zA-z0-9+/=]+)"', preload_codes)
        base64_fragments.remove('init')

        def _check_sequence(cur_fragments):
            if not cur_fragments:
                return
            for i in range(len(cur_fragments)):
                cur_sequence = (''.join(cur_fragments[i:] + cur_fragments[:i])).encode('ascii')
                try:
                    raw_data = base64.b64decode(cur_sequence)
                    if compat_ord(raw_data[0]) == compat_ord('{'):
                        return json.loads(raw_data.decode('utf-8'))
                except (TypeError, binascii.Error, UnicodeDecodeError, ValueError):
                    continue

        def _check_data():
            for i in range(len(base64_fragments) + 1):
                for j in range(i, len(base64_fragments) + 1):
                    data = _check_sequence(base64_fragments[:i] + base64_fragments[j:])
                    if data:
                        return data

        self.to_screen('Try to compute possible data sequence. This may take some time.')
        data = _check_data()

        if not data:
            raise ExtractorError(
                'Preload information could not be extracted', expected=True)

        formats = []
        get_quality = qualities(['500k', '480p', '1000k', '720p', '1080p'])
        for filed in data['files']:
            if determine_ext(filed['url']) == 'm3u8':
                # compat_urllib_parse.urljoin does not work here
                if filed['url'].startswith('/'):
                    m3u8_url = 'http://ht.cdn.turner.com/tbs/big/teamcoco' + filed['url']
                else:
                    m3u8_url = filed['url']
                m3u8_formats = self._extract_m3u8_formats(
                    m3u8_url, video_id, ext='mp4')
                for m3u8_format in m3u8_formats:
                    if m3u8_format not in formats:
                        formats.append(m3u8_format)
            elif determine_ext(filed['url']) == 'f4m':
                # TODO Correct f4m extraction
                continue
            else:
                if filed['url'].startswith('/mp4:protected/'):
                    # TODO Correct extraction for these files
                    continue
                m_format = re.search(r'(\d+(k|p))\.mp4', filed['url'])
                if m_format is not None:
                    format_id = m_format.group(1)
                else:
                    format_id = filed['bitrate']
                tbr = (
                    int(filed['bitrate'])
                    if filed['bitrate'].isdigit()
                    else None)

                formats.append({
                    'url': filed['url'],
                    'ext': 'mp4',
                    'tbr': tbr,
                    'format_id': format_id,
                    'quality': get_quality(format_id),
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'title': data['title'],
            'thumbnail': data.get('thumb', {}).get('href'),
            'description': data.get('teaser'),
            'duration': data.get('duration'),
            'age_limit': self._family_friendly_search(webpage),
        }

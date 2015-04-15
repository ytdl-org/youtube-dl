# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
)


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
        webpage = self._download_webpage(url, display_id)

        video_id = mobj.group('video_id')
        if not video_id:
            video_id = self._html_search_regex(
                self._VIDEO_ID_REGEXES, webpage, 'video id')

        preload = None
        preloads = re.findall(r'"preload":\s*"([^"]+)"', webpage)
        if preloads:
            preload = max([(len(p), p) for p in preloads])[1]

        if not preload:
            preload = ''.join(re.findall(r'this\.push\("([^"]+)"\);', webpage))

        if not preload:
            preload = self._html_search_regex([
                r'player,\[?"([^"]+)"\]?', r'player.init\(\[?"([^"]+)"\]?\)'
            ], webpage.replace('","', ''), 'preload data', default=None)

        if not preload:
            raise ExtractorError(
                'Preload information could not be extracted', expected=True)

        data = self._parse_json(
            base64.b64decode(preload.encode('ascii')).decode('utf-8'), video_id)

        formats = []
        get_quality = qualities(['500k', '480p', '1000k', '720p', '1080p'])
        for filed in data['files']:
            if filed['type'] == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    filed['url'], video_id, ext='mp4'))
            else:
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

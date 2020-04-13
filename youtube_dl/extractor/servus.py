# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError, JSON_LD_RE


class ServusIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            servus\.com/(?:(?:at|de)/p/[^/]+|tv/videos)|
                            servustv\.com/videos
                        )
                        /(?P<id>[aA]{2}-\w+|\d+-\d+)
                    '''
    _TESTS = [{
        # new URL schema
        'url': 'https://www.servustv.com/videos/aa-1t6vbu5pw1w12/',
        'md5': '9f825d6ec14b3d8bebc5b23d094e1e51',
        'info_dict': {
            'id': 'AA-1T6VBU5PW1W12',
            'ext': 'mp4',
            'title': 'Die Grünen aus Sicht des Volkes',
            'description': 'md5:1247204d85783afe3682644398ff2ec4',
            'upload_date': '20170911',
            'timestamp': 1505147648,
        }
    }, {
        # old URL schema
        'url': 'https://www.servus.com/de/p/Die-Gr%C3%BCnen-aus-Sicht-des-Volkes/AA-1T6VBU5PW1W12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/at/p/Wie-das-Leben-beginnt/1309984137314-381415152/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/aa-1t6vbu5pw1w12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/1380889096408-1235196658/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).upper()
        webpage = self._download_webpage(url, video_id)

        if 'rbmh-video-player-trigger' not in webpage:
            raise ExtractorError('Video not available (maybe not aired yet)', expected=True, video_id=video_id)

        info = {}
        for match in re.finditer(JSON_LD_RE, webpage):
            json_ld = match.group('json_ld')
            info = self._json_ld(json_ld, video_id)
            if info:
                break
        else:
            raise ExtractorError('Could not extract video URL', video_id=video_id)

        info['id'] = video_id
        info['formats'] = self._extract_m3u8_formats(info['url'], video_id, 'mp4')
        self._sort_formats(info['formats'])

        return info

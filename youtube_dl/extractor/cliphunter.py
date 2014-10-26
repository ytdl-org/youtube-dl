from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


_translation_table = {
    'a': 'h', 'd': 'e', 'e': 'v', 'f': 'o', 'g': 'f', 'i': 'd', 'l': 'n',
    'm': 'a', 'n': 'm', 'p': 'u', 'q': 't', 'r': 's', 'v': 'p', 'x': 'r',
    'y': 'l', 'z': 'i',
    '$': ':', '&': '.', '(': '=', '^': '&', '=': '/',
}


def _decode(s):
    return ''.join(_translation_table.get(c, c) for c in s)


class CliphunterIE(InfoExtractor):
    IE_NAME = 'cliphunter'

    _VALID_URL = r'''(?x)http://(?:www\.)?cliphunter\.com/w/
        (?P<id>[0-9]+)/
        (?P<seo>.+?)(?:$|[#\?])
    '''
    _TEST = {
        'url': 'http://www.cliphunter.com/w/1012420/Fun_Jynx_Maze_solo',
        'md5': 'a2ba71eebf523859fe527a61018f723e',
        'info_dict': {
            'id': '1012420',
            'ext': 'mp4',
            'title': 'Fun Jynx Maze solo',
            'thumbnail': 're:^https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._search_regex(
            r'mediaTitle = "([^"]+)"', webpage, 'title')

        pl_fiji = self._search_regex(
            r'pl_fiji = \'([^\']+)\'', webpage, 'video data')
        pl_c_qual = self._search_regex(
            r'pl_c_qual = "(.)"', webpage, 'video quality')
        video_url = _decode(pl_fiji)
        formats = [{
            'url': video_url,
            'format_id': 'default-%s' % pl_c_qual,
        }]

        qualities_json = self._search_regex(
            r'var pl_qualities\s*=\s*(.*?);\n', webpage, 'quality info')
        qualities_data = json.loads(qualities_json)

        for i, t in enumerate(
                re.findall(r"pl_fiji_([a-z0-9]+)\s*=\s*'([^']+')", webpage)):
            quality_id, crypted_url = t
            video_url = _decode(crypted_url)
            f = {
                'format_id': quality_id,
                'url': video_url,
                'quality': i,
            }
            if quality_id in qualities_data:
                qd = qualities_data[quality_id]
                m = re.match(
                    r'''(?x)<b>(?P<width>[0-9]+)x(?P<height>[0-9]+)<\\/b>
                        \s*\(\s*(?P<tbr>[0-9]+)\s*kb\\/s''', qd)
                if m:
                    f['width'] = int(m.group('width'))
                    f['height'] = int(m.group('height'))
                    f['tbr'] = int(m.group('tbr'))
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r"var\s+mov_thumb\s*=\s*'([^']+)';",
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
            'thumbnail': thumbnail,
        }

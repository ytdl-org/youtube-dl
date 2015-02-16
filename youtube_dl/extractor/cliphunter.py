from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import determine_ext


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
        'md5': 'b7c9bbd4eb3a226ab91093714dcaa480',
        'info_dict': {
            'id': '1012420',
            'ext': 'flv',
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

        fmts = {}
        for fmt in ('mp4', 'flv'):
            fmt_list = self._parse_json(self._search_regex(
                r'var %sjson\s*=\s*(\[.*?\]);' % fmt, webpage, '%s formats' % fmt), video_id)
            for f in fmt_list:
                fmts[f['fname']] = _decode(f['sUrl'])

        qualities = self._parse_json(self._search_regex(
            r'var player_btns\s*=\s*(.*?);\n', webpage, 'quality info'), video_id)

        formats = []
        for fname, url in fmts.items():
            f = {
                'url': url,
            }
            if fname in qualities:
                qual = qualities[fname]
                f.update({
                    'format_id': '%s_%sp' % (determine_ext(url), qual['h']),
                    'width': qual['w'],
                    'height': qual['h'],
                    'tbr': qual['br'],
                })
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

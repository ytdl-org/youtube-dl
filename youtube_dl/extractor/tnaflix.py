from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    str_to_int,
)

class TNAFlixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tnaflix\.com/(?P<cat_id>[\w-]+)/(?P<display_id>[\w-]+)/video(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.tnaflix.com/porn-stars/Carmella-Decesare-striptease/video553878',
        'md5': 'ecf3498417d09216374fc5907f9c6ec0',
        'info_dict': {
            'id': '553878',
            'display_id': 'Carmella-Decesare-striptease',
            'ext': 'mp4',
            'title': 'Carmella Decesare - striptease',
            'thumbnail': 're:https?://.*\.jpg$',
            #'duration': 84,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        redir_url = self._html_search_regex(
            r'flashvars.config = escape\("([^"]+)"', webpage, 'redirection URL')
        redirection_webpage = self._download_webpage(redir_url, display_id)
        sources = self._search_regex(
            r'<quality>(.+)</quality>', redirection_webpage, 'sources', flags=re.MULTILINE|re.DOTALL)
        
        formats = []
        for format_id, video_url in re.findall(r'<res>([^<]+)</res>\s*<videoLink>([^<]+)</videoLink>', sources, flags=re.MULTILINE|re.DOTALL):
            fmt = {
                'url': video_url,
                'format_id': format_id,
            }
            m = re.search(r'^(\d+)', format_id)
            if m:
                fmt['height'] = int(m.group(1))
            formats.append(fmt)
        self._sort_formats(formats)
        
        title = self._og_search_title(webpage)
        
        #duration = self._html_search_regex(r'<meta itemprop="duration" content="T(\d+)M(\d+)S"', webpage, 'duration')

        thumbnail = self._html_search_regex(
            r'<meta\s+itemprop="thumbnailUrl"\s+content="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            #'duration': duration,
            'age_limit': self._rta_search(webpage),
        }

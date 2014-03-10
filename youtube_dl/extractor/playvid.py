from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)


class PlayvidIE(InfoExtractor):
    _VALID_URL = r'^https?://www\.playvid\.com/watch(\?v=|/)(?P<id>.+?)(?:#|$)'
    _TEST = {
        'url': 'http://www.playvid.com/watch/agbDDi7WZTV',
        'md5': '44930f8afa616efdf9482daf4fe53e1e',
        'info_dict': {
            'id': 'agbDDi7WZTV',
            'ext': 'mp4',
            'title': 'Michelle Lewin in Miami Beach',
            'duration': 240,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_title = None
        duration = None
        video_thumbnail = None
        formats = []

        # most of the information is stored in the flashvars
        flashvars = self._html_search_regex(
            r'flashvars="(.+?)"', webpage, 'flashvars')

        infos = compat_urllib_parse.unquote(flashvars).split(r'&')
        for info in infos:
            videovars_match = re.match(r'^video_vars\[(.+?)\]=(.+?)$', info)
            if videovars_match:
                key = videovars_match.group(1)
                val = videovars_match.group(2)

                if key == 'title':
                    video_title = compat_urllib_parse.unquote_plus(val)
                if key == 'duration':
                    try:
                        duration = int(val)
                    except ValueError:
                        pass
                if key == 'big_thumb':
                    video_thumbnail = val

                videourl_match = re.match(
                    r'^video_urls\]\[(?P<resolution>[0-9]+)p', key)
                if videourl_match:
                    height = int(videourl_match.group('resolution'))
                    formats.append({
                        'height': height,
                        'url': val,
                    })
        self._sort_formats(formats)

        # Extract title - should be in the flashvars; if not, look elsewhere
        if video_title is None:
            video_title = self._html_search_regex(
                r'<title>(.*?)</title', webpage, 'title')

        return {
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'duration': duration,
            'description': None,
            'age_limit': 18
        }

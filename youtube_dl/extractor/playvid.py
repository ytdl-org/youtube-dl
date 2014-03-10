from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    determine_ext,
)

class PlayvidIE(InfoExtractor):

    _VALID_URL = r'^(?:https?://)?www\.playvid\.com/watch(\?v=|/)(?P<id>.+?)(#|$)'
    _TEST = {
        'url': 'http://www.playvid.com/watch/agbDDi7WZTV',
        'file': 'agbDDi7WZTV.mp4',
        'md5': '44930f8afa616efdf9482daf4fe53e1e',
        'info_dict': {
            'title': 'Michelle Lewin in Miami Beach',
            'duration': 240,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_title = None
        duration = None
        video_thumbnail = None
        formats = []

        # most of the information is stored in the flashvars
        flashvars_match = re.search(r'flashvars="(.+?)"',webpage)

        if flashvars_match:
            infos = compat_urllib_parse.unquote(flashvars_match.group(1)).split(r'&amp;')
            for info in infos:
                videovars_match = re.match(r'^video_vars\[(.+?)\]=(.+?)$',info)
                if videovars_match:
                    key = videovars_match.group(1)
                    val = videovars_match.group(2)

                    if key == 'title':
                        video_title = val.replace('+',' ')
                    if key == 'duration':
                        try:
                            duration = val
                        except ValueError:
                            duration = None
                    if key == 'big_thumb':
                        video_thumbnail = val

                    videourl_match = re.match(r'^video_urls\]\[(?P<resolution>\d+)p',key)
                    if videourl_match:
                        resolution = int(videourl_match.group('resolution'))
                        formats.append({
                            'resolution': resolution,            # 360, 480, ...
                            'ext': determine_ext(val),
                            'url': val
                        })

        # fatal error, if no download url is found
        if len(formats) == 0:
            raise ExtractorError,'no video url found'

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

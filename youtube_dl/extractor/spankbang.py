# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re

class SpankBangIE(InfoExtractor):
    """Extractor for http://spankbang.com"""
    
    _VALID_URL = r"https?://(?:www\.)?spankbang\.com/(?P<id>\w+)/video/.*"

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r"<h1>(?:<img.+?>)?(.*?)</h1>", webpage, "title")
        
        stream_key = self._html_search_regex(r"""var\s+stream_key\s*[=]\s*['"](.+?)['"]\s*;""", webpage, "stream_key")
        
        qualities = re.findall(r"<span.+?>([0-9]+p).*?</span>", webpage)
        
        formats = []
        for q in sorted(qualities):
            formats.append({
                "format_id": q,
                "format": q,
                "ext": "mp4",
                "url": "http://spankbang.com/_{}/{}/title/{}__mp4".format(video_id, stream_key, q)
            })

        return {
            "id": video_id,
            "title": title,
            "description": self._og_search_description(webpage),
            "formats": formats
        }

# vim: tabstop=4 expandtab

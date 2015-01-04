from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    get_element_by_attribute,
    unescapeHTML
)


class GoGoAnimeIE(InfoExtractor):
    IE_NAME = 'gogoanime'
    IE_DESC = 'GoGoAnime'
    _VALID_URL = r'http://www.gogoanime.com/(?P<id>[A-Za-z0-9-]+)'

    _TEST = {
        'url': 'http://www.gogoanime.com/mahou-shoujo-madoka-magica-movie-1',
        'info_dict': {
            'id': 'mahou-shoujo-madoka-magica-movie-1'
        },
        'playlist_count': 3
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)

        if 'Oops! Page Not Found</font>' in page:
            raise ExtractorError('Video does not exist', expected=True)

        content = get_element_by_attribute("class", "postcontent", page)
        vids = re.findall(r'<iframe[^>]*?src=[\'"](h[^\'"]+)[\'"]', content)
        vids = [
            unescapeHTML(compat_urllib_parse.unquote(x))
            for x in vids if not re.search(r".*videofun.*", x)]

        if re.search(r'<div class="postcontent">[^<]*<p><iframe src=[\'"][^>]+></iframe><br />', page):
            return self.playlist_result([self.url_result(vid) for vid in vids], video_id)

        title = self._html_search_regex(
            r'<div class="postdesc">[^<]*<h1>([^<]+)</h1>', page, 'title')

        return {
            '_type': 'url',
            'id': video_id,
            'url': vids[0],
            'title': title,
        }


class GoGoAnimeSearchIE(InfoExtractor):
    IE_NAME = 'gogoanime:search'
    IE_DESC = 'GoGoAnime Search'

    _VALID_URL = r'http://www\.gogoanime\.com/.*\?s=(?P<id>[^&]*)'
    _TEST = {
        'url': 'http://www.gogoanime.com/?s=bokusatsu',
        'info_dict': {
            'id': 'bokusatsu'
        },
        'playlist_count': 6
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        posts = re.findall(
            r'<div class="postlist">[^<]*<p[^>]*>[^<]*<a href="(?P<url>[^"]+)"',
            webpage)

        return self.playlist_result(
            [self.url_result(p) for p in posts], playlist_id)

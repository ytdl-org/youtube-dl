from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urlparse,
    compat_urllib_parse,
    get_element_by_attribute,
    unescapeHTML
)


class GoGoAnimeIE(InfoExtractor):
    IE_NAME = 'gogoanime'
    IE_DESC = 'GoGoAnime'

    _VALID_URL = r'http://www.gogoanime.com/(?P<id>[A-Za-z0-9-]+)'

    _NOT_FOUND_REGEX = r'Oops! Page Not Found</font>'
    _FILEKEY_REGEX = r'flashvars\.filekey="(?P<filekey>[^"]+)";'
    _TITLE_REGEX = r'<div class="postdesc">[^<]*<h1>([^<]+)</h1>'

    _SINGLEPART_REGEX = r'<div class="postcontent">[^<]*<p><iframe src=[\'"][^>]+></iframe></p>'
    _MULTIPART_REGEX = r'<div class="postcontent">[^<]*<p><iframe src=[\'"][^>]+></iframe><br />'
    _POSTCONTENT_REGEX = r'<div class="postcontent">(?P<content>(?!</div>)*)</div>'
    _IFRAME_REGEX = r'<iframe[^>]*src=[\'"](h[^\'"]+)[\'"]'

    """_TEST = {
        'url': 'http://www.gogoanime.com/mahou-shoujo-madoka-magica-episode-12',
        'md5': 'd9b511f92ce9348206f8481ba19dc9f1',
        'info_dict': {
            'id': 'Mahou-Shoujo-Madoka-Magica-12',
            'ext': 'flv',
            'title': 'Mahou-Shoujo-Madoka-Magica-12',
            'description': 'Mahou-Shoujo-Madoka-Magica-12'
        }
    },"""
    _TEST = {
        'url': 'http://www.gogoanime.com/mahou-shoujo-madoka-magica-movie-1',
        'info_dict': {
            'id': 'mahou-shoujo-madoka-magica-movie-1'
        },
        'playlist_count': 3
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, "Downloading video page")

        if re.search(self._NOT_FOUND_REGEX, page) is not None:
            raise ExtractorError('Video does not exist', expected=True)

        title = self._html_search_regex(self._TITLE_REGEX, page, 'title', fatal=False)
        description = title

        content = get_element_by_attribute("class", "postcontent", page)

        pattern = re.compile(self._IFRAME_REGEX)
        vids = pattern.findall(content)

        vids = [unescapeHTML(compat_urllib_parse.unquote(x)) for x in vids if not re.search(".*videofun.*", x)]

        if (re.search(self._SINGLEPART_REGEX, page)):
            return {
                '_type': 'url',
                'id': None,
                'url': vids[0],
                'title': title,
                'description': title
            }

        if (re.search(self._MULTIPART_REGEX, page)):
            return self.playlist_result([self.url_result(vid) for vid in vids], video_id)

        print("Error parsing!")
        return {}


class GoGoAnimeSearchIE(InfoExtractor):
    IE_NAME = 'gogoanime:search'
    IE_DESC = 'GoGoAnime Search'

    _VALID_URL = r'http://www\.gogoanime\.com/.*\?s=(?P<id>.*)'

    _POSTLIST_REGEX = r'<div class="postlist">[^<]*<p[^>]*>[^<]*<a href="(?P<url>[^"]+)"'

    _TEST = {
        'url': 'http://www.gogoanime.com/?s=bokusatsu',
        'info_dict': {
            'id': 'bokusatsu'
        },
        'playlist_count': 6
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, "Downloading video page")

        pattern = re.compile(self._POSTLIST_REGEX)
        content = pattern.findall(page)

        return self.playlist_result([self.url_result(vid) for vid in content], video_id)


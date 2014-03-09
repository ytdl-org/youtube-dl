from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    RegexNotFoundError,
    unescapeHTML,
)


class JukeboxIE(InfoExtractor):
    _VALID_URL = r'^http://www\.jukebox?\..+?\/.+[,](?P<video_id>[a-z0-9\-]+)\.html'
    _TEST = {
        'url': 'http://www.jukebox.es/kosheen/videoclip,pride,r303r.html',
        'md5': '5dc6477e74b1e37042ac5acedd8413e5',
        'info_dict': {
            'id': 'r303r',
            'ext': 'flv',
            'title': 'Kosheen-En Vivo Pride',
            'uploader': 'Kosheen',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        html = self._download_webpage(url, video_id)
        iframe_url = unescapeHTML(self._search_regex(r'<iframe .*src="([^"]*)"', html, 'iframe url'))

        iframe_html = self._download_webpage(iframe_url, video_id, 'Downloading iframe')
        if re.search(r'class="jkb_waiting"', iframe_html) is not None:
            raise ExtractorError('Video is not available(in your country?)!')

        self.report_extraction(video_id)

        try:
            video_url = self._search_regex(r'"config":{"file":"(?P<video_url>http:[^"]+\?mdtk=[0-9]+)"',
                iframe_html, 'video url')
            video_url = unescapeHTML(video_url).replace('\/', '/')
        except RegexNotFoundError:
            youtube_url = self._search_regex(
                r'config":{"file":"(http:\\/\\/www\.youtube\.com\\/watch\?v=[^"]+)"',
                iframe_html, 'youtube url')
            youtube_url = unescapeHTML(youtube_url).replace('\/', '/')
            self.to_screen('Youtube video detected')
            return self.url_result(youtube_url, ie='Youtube')

        title = self._html_search_regex(r'<h1 class="inline">([^<]+)</h1>',
            html, 'title')
        artist = self._html_search_regex(r'<span id="infos_article_artist">([^<]+)</span>',
            html, 'artist')

        return {
            'id': video_id,
            'url': video_url,
            'title': artist + '-' + title,
            'uploader': artist,
        }

# coding: utf-8
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)

class JukeboxIE(InfoExtractor):
    _VALID_URL = r'^http://www\.jukebox?\..+?\/.+[,](?P<video_id>[a-z0-9\-]+).html'
    _IFRAME = r'<iframe .*src="(?P<iframe>[^"]*)".*>'
    _VIDEO_URL = r'"config":{"file":"(?P<video_url>http:[^"]+[.](?P<video_ext>[^.?]+)[?]mdtk=[0-9]+)"'
    _TITLE = r'<h1 class="inline">(?P<title>[^<]+)</h1>.*<span id="infos_article_artist">(?P<artist>[^<]+)</span>'
    _IS_YOUTUBE = r'config":{"file":"(?P<youtube_url>http:[\\][/][\\][/]www[.]youtube[.]com[\\][/]watch[?]v=[^"]+)"'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        html = self._download_webpage(url, video_id)

        mobj = re.search(self._IFRAME, html)
        if mobj is None:
            raise ExtractorError(u'Cannot extract iframe url')
        iframe_url = unescapeHTML(mobj.group('iframe'))

        iframe_html = self._download_webpage(iframe_url, video_id, 'Downloading iframe')
        mobj = re.search(r'class="jkb_waiting"', iframe_html)
        if mobj is not None:
            raise ExtractorError(u'Video is not available(in your country?)!')

        self.report_extraction(video_id)

        mobj = re.search(self._VIDEO_URL, iframe_html)
        if mobj is None:
            mobj = re.search(self._IS_YOUTUBE, iframe_html)
            if mobj is None:
                raise ExtractorError(u'Cannot extract video url')
            youtube_url = unescapeHTML(mobj.group('youtube_url')).replace('\/','/')
            self.to_screen(u'Youtube video detected')
            return self.url_result(youtube_url,ie='Youtube')
        video_url = unescapeHTML(mobj.group('video_url')).replace('\/','/')
        video_ext = unescapeHTML(mobj.group('video_ext'))

        mobj = re.search(self._TITLE, html)
        if mobj is None:
            raise ExtractorError(u'Cannot extract title')
        title = unescapeHTML(mobj.group('title'))
        artist = unescapeHTML(mobj.group('artist'))

        return [{'id': video_id,
                 'url': video_url,
                 'title': artist + '-' + title,
                 'ext': video_ext
                 }]

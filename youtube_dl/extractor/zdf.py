import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)

class ZDFIE(InfoExtractor):
    _VALID_URL = r'^http://www\.zdf\.de\/ZDFmediathek\/(.*beitrag\/video\/)(?P<video_id>[^/\?]+)(?:\?.*)?'
    _TITLE = r'<h1(?: class="beitragHeadline")?>(?P<title>.*)</h1>'
    _MEDIA_STREAM = r'<a href="(?P<video_url>.+(?P<media_type>.streaming).+/zdf/(?P<quality>[^\/]+)/[^"]*)".+class="play".+>'
    _MMS_STREAM = r'href="(?P<video_url>mms://[^"]*)"'
    _RTSP_STREAM = r'(?P<video_url>rtsp://[^"]*.mp4)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('video_id')

        html = self._download_webpage(url, video_id)
        streams = [m.groupdict() for m in re.finditer(self._MEDIA_STREAM, html)]
        if streams is None:
            raise ExtractorError(u'No media url found.')

        # s['media_type'] == 'wstreaming' -> use 'Windows Media Player' and mms url
        # s['media_type'] == 'hstreaming' -> use 'Quicktime' and rtsp url
        # choose first/default media type and highest quality for now
        for s in streams:        #find 300 - dsl1000mbit
            if s['quality'] == '300' and s['media_type'] == 'wstreaming':
                stream_=s
                break
        for s in streams:        #find veryhigh - dsl2000mbit
            if s['quality'] == 'veryhigh' and s['media_type'] == 'wstreaming': # 'hstreaming' - rtsp is not working
                stream_=s
                break
        if stream_ is None:
            raise ExtractorError(u'No stream found.')

        media_link = self._download_webpage(stream_['video_url'], video_id,'Get stream URL')

        self.report_extraction(video_id)
        mobj = re.search(self._TITLE, html)
        if mobj is None:
            raise ExtractorError(u'Cannot extract title')
        title = unescapeHTML(mobj.group('title'))

        mobj = re.search(self._MMS_STREAM, media_link)
        if mobj is None:
            mobj = re.search(self._RTSP_STREAM, media_link)
            if mobj is None:
                raise ExtractorError(u'Cannot extract mms:// or rtsp:// URL')
        mms_url = mobj.group('video_url')

        mobj = re.search('(.*)[.](?P<ext>[^.]+)', mms_url)
        if mobj is None:
            raise ExtractorError(u'Cannot extract extention')
        ext = mobj.group('ext')

        return [{'id': video_id,
                 'url': mms_url,
                 'title': title,
                 'ext': ext
                 }]

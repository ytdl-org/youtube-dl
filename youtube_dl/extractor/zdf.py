import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
)


class ZDFIE(InfoExtractor):
    _VALID_URL = r'^http://www\.zdf\.de\/ZDFmediathek(?P<hash>#)?\/(.*beitrag\/video\/)(?P<video_id>[^/\?]+)(?:\?.*)?'
    _MEDIA_STREAM = r'<a href="(?P<video_url>.+(?P<media_type>.streaming).+/zdf/(?P<quality>[^\/]+)/[^"]*)".+class="play".+>'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('video_id')

        if mobj.group('hash'):
            url = url.replace(u'#', u'', 1)

        html = self._download_webpage(url, video_id)
        streams = [m.groupdict() for m in re.finditer(self._MEDIA_STREAM, html)]
        if streams is None:
            raise ExtractorError(u'No media url found.')

        # s['media_type'] == 'wstreaming' -> use 'Windows Media Player' and mms url
        # s['media_type'] == 'hstreaming' -> use 'Quicktime' and rtsp url
        # choose first/default media type and highest quality for now
        def stream_pref(s):
            TYPE_ORDER = ['ostreaming', 'hstreaming', 'wstreaming']
            try:
                type_pref = TYPE_ORDER.index(s['media_type'])
            except ValueError:
                type_pref = 999

            QUALITY_ORDER = ['veryhigh', '300']
            try:
                quality_pref = QUALITY_ORDER.index(s['quality'])
            except ValueError:
                quality_pref = 999

            return (type_pref, quality_pref)

        sorted_streams = sorted(streams, key=stream_pref)
        if not sorted_streams:
            raise ExtractorError(u'No stream found.')
        stream = sorted_streams[0]

        media_link = self._download_webpage(
            stream['video_url'],
            video_id,
            u'Get stream URL')

        #MMS_STREAM = r'href="(?P<video_url>mms://[^"]*)"'
        RTSP_STREAM = r'(?P<video_url>rtsp://[^"]*.mp4)'

        mobj = re.search(self._MEDIA_STREAM, media_link)
        if mobj is None:
            mobj = re.search(RTSP_STREAM, media_link)
            if mobj is None:
                raise ExtractorError(u'Cannot extract mms:// or rtsp:// URL')
        video_url = mobj.group('video_url')

        title = self._html_search_regex(
            r'<h1(?: class="beitragHeadline")?>(.*?)</h1>',
            html, u'title')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': determine_ext(video_url)
        }

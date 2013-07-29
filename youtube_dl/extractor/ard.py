import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class ARDIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:(?:www\.)?ardmediathek\.de|mediathek\.daserste\.de)/(?:.*/)(?P<video_id>[^/\?]+)(?:\?.*)?'
    _TITLE = r'<h1(?: class="boxTopHeadline")?>(?P<title>.*)</h1>'
    _MEDIA_STREAM = r'mediaCollection\.addMediaStream\((?P<media_type>\d+), (?P<quality>\d+), "(?P<rtmp_url>[^"]*)", "(?P<video_url>[^"]*)", "[^"]*"\)'
    _TEST = {
        u'url': u'http://www.ardmediathek.de/das-erste/tagesschau-in-100-sek?documentId=14077640',
        u'file': u'14077640.mp4',
        u'md5': u'6ca8824255460c787376353f9e20bbd8',
        u'info_dict': {
            u"title": u"11.04.2013 09:23 Uhr - Tagesschau in 100 Sekunden"
        },
        u'skip': u'Requires rtmpdump'
    }

    def _real_extract(self, url):
        # determine video id from url
        m = re.match(self._VALID_URL, url)

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        # determine title and media streams from webpage
        html = self._download_webpage(url, video_id)
        title = re.search(self._TITLE, html).group('title')
        streams = [mo.groupdict() for mo in re.finditer(self._MEDIA_STREAM, html)]
        if not streams:
            assert '"fsk"' in html
            raise ExtractorError(u'This video is only available after 8:00 pm')

        # choose default media type and highest quality for now
        stream = max([s for s in streams if int(s["media_type"]) == 0],
                     key=lambda s: int(s["quality"]))

        # there's two possibilities: RTMP stream or HTTP download
        info = {'id': video_id, 'title': title, 'ext': 'mp4'}
        if stream['rtmp_url']:
            self.to_screen(u'RTMP download detected')
            assert stream['video_url'].startswith('mp4:')
            info["url"] = stream["rtmp_url"]
            info["play_path"] = stream['video_url']
        else:
            assert stream["video_url"].endswith('.mp4')
            info["url"] = stream["video_url"]
        return [info]

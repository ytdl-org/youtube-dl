import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class MDRIE(InfoExtractor):
    _VALID_URL = r'^(?P<domain>(?:https?://)?(?:www\.)?mdr\.de)/mediathek/(?:.*)/(?P<type>video|audio)(?P<video_id>[^/_]+)_.*'
    _TITLE = r'<h2>(?P<title1>[^<]+)<span>(?P<title2>[^<]+)</span></h2>'

    _MEDIA_XML = r'(?P<xmlurl>/mediathek/(.+)/(video|audio)([0-9]+)-avCustom.xml)'
    _MEDIA_STREAM_VIDEO = r'<asset>.*<frameWidth>(?P<frameWidth>[0-9]+)</frameWidth>.*<flashMediaServerApplicationURL>(?P<flashMediaServerApplicationURL>[^<]+)</flashMediaServerApplicationURL><flashMediaServerURL>(?P<flashMediaServerURL>[^<]+)</flashMediaServerURL>.*<progressiveDownloadUrl>(?P<progressiveDownloadUrl>[^<]+)</progressiveDownloadUrl></asset>'
    _MEDIA_STREAM_AUDIO = r'<asset>.*<mediaType>(?P<mediaType>[A-Z0-9]+)</mediaType><bitrateAudio>(?P<bitrateAudio>[0-9]+)</bitrateAudio>.*<flashMediaServerApplicationURL>(?P<flashMediaServerApplicationURL>[^<]+)</flashMediaServerApplicationURL><flashMediaServerURL>(?P<flashMediaServerURL>[^<]+)</flashMediaServerURL>.*<progressiveDownloadUrl>(?P<progressiveDownloadUrl>[^<]+)</progressiveDownloadUrl></asset>'
    _TESTS = [{
        u'url': u'http://www.mdr.de/mediathek/themen/nachrichten/video165624_zc-c5c7de76_zs-3795826d.html',
        u'file': u'165624.mp4',
        u'md5': u'95165945756198b8fa2dea10f0b04614',
        u'info_dict': {
            u"title": u"MDR aktuell Eins30 09.12.2013, 22:48 Uhr"
        },
        #u'skip': u'Requires rtmpdump'    # rtmp is optional
    },
    {
        u'url': u' http://www.mdr.de/mediathek/radio/mdr1-radio-sachsen/audio718370_zc-67b21197_zs-1b9b2483.html',
        u'file': u'718370.mp4',
        u'md5': u'4a5b1fbb5519fb0d929c384b6ff7cb8b',
        u'info_dict': {
            u"title": u"MDR 1 RADIO SACHSEN 10.12.2013, 05:00 Uhr"
        },
        #u'skip': u'Requires rtmpdump'    # rtmp is optional
    }]

    def _real_extract(self, url):

        # determine video id from url
        m = re.match(self._VALID_URL, url)
        video_id = m.group('video_id')
        domain = m.group('domain')
        mediatype = m.group('type')

        # determine title and media streams from webpage
        html = self._download_webpage(url, video_id)
        t = re.search(self._TITLE, html)
        if not t:
            raise ExtractorError(u'no title found')
        title = t.group('title1') + t.group('title2')
        m = re.search(self._MEDIA_XML, html)
        if not m:
            raise ExtractorError(u'no xml found')
        xmlurl = m.group('xmlurl')
        xml = self._download_webpage(domain+xmlurl, video_id, 'download XML').replace('\n','').replace('\r','').replace('<asset>','\n<asset>').replace('</asset>','</asset>\n')
        if(mediatype == "video"):
            streams = [mo.groupdict() for mo in re.finditer(self._MEDIA_STREAM_VIDEO, xml)]
            if not streams:
                raise ExtractorError(u'no media found')
            # choose default media type and highest quality for now
            stream = max([s for s in streams if s["progressiveDownloadUrl"].startswith("http://") ],
                         key=lambda s: int(s["frameWidth"]))
        else:
            streams = [mo.groupdict() for mo in re.finditer(self._MEDIA_STREAM_AUDIO, xml)]
            if not streams:
                raise ExtractorError(u'no media found')
            # choose default media type (MP4) and highest quality for now
            stream = max([s for s in streams if s["progressiveDownloadUrl"].startswith("http://") and s["mediaType"] == "MP4" ],
                         key=lambda s: int(s["bitrateAudio"]))

        # there's two possibilities: RTMP stream or HTTP download
        info = {'id': video_id, 'title': title, 'ext': 'mp4'}
        if not stream["progressiveDownloadUrl"]:
            self.to_screen(u'RTMP download detected')
            assert stream['flashMediaServerURL'].startswith('mp4:')
            info["url"] = stream["flashMediaServerApplicationURL"]
            info["play_path"] = stream['flashMediaServerURL']
        else:
            assert stream["progressiveDownloadUrl"].endswith('.mp4')
            info["url"] = stream["progressiveDownloadUrl"]
        return [info]

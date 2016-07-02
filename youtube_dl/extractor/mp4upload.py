# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re
import time


class Mp4UploadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mp4upload\.com/(?P<id>.+)'
    _TEST = {
        'url': 'http://www.mp4upload.com/e52ycvdl4x29',
        'md5': '09780a74b0de79ada5f9a8955f0704fc',

        'info_dict': {
            'id': 'e52ycvdl4x29',
            'ext': 'mp4',
            'title': '橋本潮 - ロマンティックあげるよ.mp4',
            'timestamp': 1467471956,
            'thumbnail': 'http://www3.mp4upload.com/i/00283/e52ycvdl4x29.jpg',

            'vcodec': 'ffh264',
            'width': 454,
            'height': 360,
            'fps': 29.970,

            'acodec': 'ffaac',
            'asr': 44100,
            'abr': 96,

            # Something adds this to the _real_extract return value, and the test runner expects it present.
            # Should probably be autocalculated from the timestamp instead, just like _real_extract.
            'upload_date': '20160702',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        embedpage = self._download_webpage("http://www.mp4upload.com/embed-" + video_id + ".html", video_id)

        title = self._html_search_regex(r'<span class="dfilename">(.*?)</span>', webpage, 'title')
        url = self._html_search_regex(r'"file": "([^"]+)",', embedpage, 'url')
        thumbnail = self._html_search_regex(r'"image": "([^"]+)",', embedpage, 'url', fatal=False)

        acodec = None
        asr = None
        abr = None
        audio_raw = self._html_search_regex(
            r'<li><span class="infoname">Audio info:</span><span>(.+?)</span></li>',
            webpage, 'audioinfo', fatal=False)
        if audio_raw:
            audmatch = re.search(r'(.+?), ([0-9]+) kbps, ([0-9]+) Hz', audio_raw)
            if audmatch:
                (acodec, abr, asr) = audmatch.groups()

        # can't use _html_search_regex, there's data both inside and outside a bold tag and I need it all
        timestamp = None
        date_raw = self._search_regex(r'Uploaded on(.+?)</div>', webpage, 'timestamp', fatal=False, flags=re.DOTALL)
        if date_raw:
            date_raw = re.sub(r"<[^>]+>", "", date_raw)
            date_raw = re.sub(r"[\s]+", " ", date_raw)
            timestamp = time.mktime(time.strptime(date_raw, " %Y-%m-%d %H:%M:%S "))

        width = None
        height = None
        resolution_raw = self._html_search_regex(
            r'<li><span class="infoname">Resolution:</span><span>(.+?)</span></li>',
            webpage, 'resolution', fatal=False)
        if resolution_raw:
            resmatch = re.search(r'([0-9]+) x ([0-9]+)', resolution_raw)
            if resmatch:
                (width, height) = resmatch.groups()

        vcodec = self._html_search_regex(
            r'<li><span class="infoname">Codec:</span><span>(.+?)</span></li>',
            webpage, 'codec', fatal=False)

        fps = self._html_search_regex(
            r'<li><span class="infoname">Framerate:</span><span>(.+?) fps</span></li>',
            webpage, 'framerate', fatal=False)

        filesize_approx = self._html_search_regex(r'<span class="statd">Size</span>\s+<span>(.+?)</span>',
                                                  webpage, 'filesize', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'formats': [{
                'url': url,
                'filesize_approx': filesize_approx,

                'vcodec': vcodec,
                'width': int(width),
                'height': int(height),
                'fps': float(fps),

                'acodec': acodec,
                'asr': int(asr),
                'abr': int(abr),
            }],
            'timestamp': timestamp,
            'thumbnail': thumbnail,
        }

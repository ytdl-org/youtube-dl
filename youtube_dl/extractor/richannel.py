# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re
import urllib


class RIChannelIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?richannel\.org/(?P<id>[-a-z0-9]+)'
    _TEST = {
        'url': 'http://www.richannel.org/christmas-lectures-1991-richard-dawkins--waking-up-in-the-universe',
        'md5': '76170b1fe4eb12f5631d204a241b0bfe',
        'info_dict': {
            'id': 'christmas-lectures-1991-richard-dawkins--waking-up-in-the-universe',
            'ext': 'mp4',
            'title': str(172)  # 'CHRISTMAS LECTURES 1991: Richard Dawkins - Waking Up in the Universe', is too long to fit
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        pattern = re.compile("video id=\"player-\d+")
        reduced = pattern.search(webpage)
        patt = re.compile("[\d]+")
        r = str(reduced.group())
        m = patt.search(r)
        RiP = str(m.group())
        resolutions = ['480', '640', '960', '1280']
        valid_urls = []
        i = 0
        src = "http://theri.bc.cdn.bitgravity.com/" \
            "vid_" + RiP + "/" + RiP + "_" + resolutions[i] + ".mp4"
        redirected_url = src
        while(i < 4):
            src = "http://theri.bc.cdn.bitgravity.com/" \
                "vid_" + RiP + "/" + RiP + "_" + resolutions[i] + ".mp4"
            try:
                request = urllib.Request(src)
                opener = urllib.build_opener()
                f = opener.open(request)
                if (f.getcode() == 200):
                    redirected_url = f.url
                    valid_urls.append(redirected_url)
            except:
                pass
            formats = [{
                'quality': resolutions[i],
                'url': redirected_url,
            }]
            i += 1
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': str(RiP),
            'formats': formats,
        }

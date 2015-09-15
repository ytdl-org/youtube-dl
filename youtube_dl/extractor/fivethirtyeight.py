# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from .common import InfoExtractor
from youtube_dl.compat import compat_urllib_request
from youtube_dl import utils


class FivethirtyeightIE(InfoExtractor):
    _VALID_URL = r'http://fivethirtyeight\.com/.+'
    _TEST = {
        'url': 'http://fivethirtyeight.com/features/rage-against-the-machines/',
        'md5': 'c825a057981316c4d4444fefea35a108',
        'info_dict': {
            'id': '11694550',
            'ext': 'mp4',
            'title': 'Rage Against The Machines',
            'description': 'This is an excerpted chapter from “The Signal and the Noise: Why So Many Predictions Fail — but Some Don’t” by Nate Silver, editor in chief of FiveThirtyEight. …',
            'duration': 1037,
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'video_id')
        video_id = self._html_search_regex(r'.*data-video-id=\'(.*)\' data-cms.*', webpage, 'video_id')
        title = self._html_search_regex(r'<title>(.*)\s*\|', webpage, 'title')

        data = self._download_json(
            'http://espn.go.com/videohub/video/util/getMinifiedClipJsonById?id=%s&cms=espn&device=mobile&omniReportSuite=wdgespvideo,wdgespfivethirtyeight,wdgespge&xhr=1' % video_id, video_id)

        url = data["videos"][0]["links"]["mobile"]["href"]

        request = compat_urllib_request.Request(url)
        request.add_header('User-Agent', 'ipad')

        formats = self._extract_m3u8_formats(request, 'display_id', 'mp4')

        formats[0]["url"] = request.get_full_url()

        for idx, val in enumerate(formats):
            formats[idx]["url"] = formats[idx]["url"].replace('adsegmentlength=5', 'adsegmentlength=0')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': data["videos"][0]["posterImages"]["full"]["href"],
            'duration': utils.parse_duration(self._search_regex('mediaLength=(\d\d%3A\d\d%3A\d\d)&', data["videos"][0]["links"]["mobile"]["omniHref"], 'duration').replace('%3A', ':')),
        }

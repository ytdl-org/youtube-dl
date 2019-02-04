# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import urljoin, xpath_text


class ThisAVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisav\.com/video/(?P<id>[0-9]+)/.*'

    # all videos are now html5 videos
    _TESTS = [{
        'url': 'https://www.thisav.com/video/47734/%98%26sup1%3B%83%9E%83%82---just-fit.html',
        'md5': 'adad2d2e989b4524698b4fb856d6719f',
        'info_dict': {
            'id': '47734',
            'ext': 'mp4',
            'title': '高樹マリア - Just fit',
            'uploader': 'dj7970',
            'uploader_id': 'dj7970'
        }
    }, {
        'url': 'https://www.thisav.com/video/242352/nerdy-18yo-big-ass-tattoos-and-glasses.html',
        'md5': 'ba90c076bd0f80203679e5b60bf523ee',
        'info_dict': {
            'id': '242352',
            'ext': 'mp4',
            'title': 'Nerdy 18yo Big Ass Tattoos and Glasses',
            'uploader': 'cybersluts',
            'uploader_id': 'cybersluts',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(?:([^<]+)-\s*視頻\s*-\s*ThisAV.com\s*-\s*世界第一中文成人娛樂網站\s*|([^<]+))</title>', webpage, 'title')

        mpd_url = self._html_search_regex(
            r'"(https?://[^"]+\.mpd)"', webpage, 'MPD URL')
        mpd_root = self._download_xml(mpd_url, video_id)
        mpd_ns = self._search_regex(
            r'\{([^}]+)\}', mpd_root.tag, 'MPD namespace', default=None)
        base_url = xpath_text(mpd_root, self._xpath_ns('.//BaseURL', mpd_ns))
        video_url = urljoin(mpd_url, base_url)

        if video_url:
            info_dict = {
                'formats': [{
                    'url': video_url,
                }],
            }
        else:
            entries = self._parse_html5_media_entries(url, webpage, video_id)
            if entries:
                info_dict = entries[0]
            else:
                info_dict = self._extract_jwplayer_data(
                    webpage, video_id, require_title=False)

        uploader = self._html_search_regex(
            r': <a href="https?://www\.thisav\.com/user/[0-9]+/(?:[^"]+)">([^<]+)</a>',
            webpage, 'uploader name', fatal=False)
        uploader_id = self._html_search_regex(
            r': <a href="https?://www\.thisav\.com/user/[0-9]+/([^"]+)">(?:[^<]+)</a>',
            webpage, 'uploader id', fatal=False)

        info_dict.update({
            'id': video_id,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'title': title,
        })

        return info_dict

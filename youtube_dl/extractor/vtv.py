# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re

from ..utils import extract_attributes

class VTVIE(InfoExtractor):
    _VALID_URL = r'https?://(au|ca|cz|de|jp|kr|tw|us|vn)\.tvnet\.gov\.vn/[^/]*/(?P<id>[0-9]+)/?'
    _TESTS = [{
        # Livestream. Channel: VTV 1
        'url': 'http://us.tvnet.gov.vn/kenh-truyen-hinh/1011/vtv1',
        'info_dict': {
            'id': '1011',
            'ext': 'mp4',
            'title': r're:^VTV1 | LiveTV - TV Net [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'thumbnail': r're:https?://.*\.png$',
        }
    }, {
        # Downloading a video.
        'url': 'http://de.tvnet.gov.vn/video/109788/vtv1---bac-tuyet-tai-lao-cai-va-ha-giang/tin-nong-24h',
        'md5': '5263c63d738569ed507980f1e49ebc03',
        'info_dict': {
            'id': '109788',
            'ext': 'mp4',
            'title': 'VTV1 - Bắc tuyết tại Lào Cai và Hà Giang - TV Net',
            'thumbnail': r're:https?://.*\.JPG$',
        }
    }, {
        # Radio live stream. Channel: VOV 1
        'url': 'http://vn.tvnet.gov.vn/kenh-truyen-hinh/1014',
        'info_dict': {
            'id': '1014',
            'ext': 'm4a',
            'vcodec': 'none',
            'title': r're:VOV1 | LiveTV - TV Net [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'thumbnail': r're:https?://.*\.png$',
        }

    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title', default=None, fatal=False)
        if title is None:
            title = self._og_search_title(webpage)
        title.strip()

        mediaplayer_div = self._search_regex(r'(<div[^>]*id="mediaplayer"[^>]*>)', webpage, 'mediaplayer element')
        mediaplayer_div_attributes = extract_attributes(mediaplayer_div)

        thumbnail = mediaplayer_div_attributes.get("data-image")

        json_url = mediaplayer_div_attributes["data-file"]
        video_streams = self._download_json(json_url, video_id)


        # get any working playlist from streams. Currently there's 2 and the first always works,
        # but you never know in the future
        for stream in video_streams:
            formats = self._extract_m3u8_formats(stream.get("url"), video_id, ext="mp4", fatal=False)
            if formats:
                break

        # better support radio streams
        if title.startswith("VOV"):
            for f in formats:
                f["ext"] = "m4a"
                f["vcodec"] = "none"

        if "/video/" in url or "/radio/" in url:
            is_live = False
        elif "/kenh-truyen-hinh/" in url:
            is_live = True
        else:
            is_live = None

        if is_live:
            title = self._live_title(title)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'is_live': is_live,
        }

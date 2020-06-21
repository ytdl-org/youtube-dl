# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import ExtractorError


class PinterestIE(InfoExtractor):
    _VALID_URL = r"https?://(?:www\.)?pinterest\.(?:com|fr|de|ch|jp|cl|ca|it|co.uk|nz|ru|com.au|at|pt|co.kr|es|com.mx|dk|ph|biz|th|com.pt|com.uy|co|nl|info|kr|ie|vn|com.vn|ec|mx|in|pe|co.at|hu|co.in|co.nz|id|co.id|com.ec|com.py|engineering|tw|be|uk|com.bo|com.pe)/pin/(?P<id>[0-9]+)"
    _TEST = {
        "url": "https://www.pinterest.ca/pin/585890232762351770",
        "md5": "f51309dfca161c82a9cccb835ab10572",
        "info_dict": {
            "id": "585890232762351770",
            "ext": "mp4",
            "title": "Origami",
            "thumbnail": "https://i.pinimg.com/videos/thumbnails/originals/12/83/f0/1283f06c1c8fa040011cd7231f33f069.0000001.jpg",
            "uploader": "Sara Mashal",
            "description": "This Pin was discovered by Sara Mashal. Discover (and save!) your own Pins on Pinterest.",
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        clean_url = re.search(self._VALID_URL, url).group(0)

        webpage = self._download_webpage(clean_url, video_id)

        pin_info_json = self._search_regex(
            r"<script id=\"initial-state\" type=\"application/json\">(.+?)</script>",
            webpage,
            "Pin data JSON",
        )
        pin_info_full = json.loads(pin_info_json)
        pin_info = next(
            (
                r
                for r in pin_info_full["resourceResponses"]
                if r["name"] == "PinResource"
            ),
            None,
        )

        if pin_info:
            pin_data = pin_info["response"]["data"]
            video_urls = pin_data.get("videos", {}).get("video_list", {})
            video_data = video_urls.get("V_HLSV4")
            video_url = video_data.get("url")
            video_thumb = video_data.get("thumbnail")
            if not video_url:
                raise ExtractorError("Can't find a video stream URL")
            title = pin_data.get("title").strip() or "pinterest_video"
            pinner = pin_data.get("pinner", {})
            uploader = pinner.get("full_name") or pinner.get("username")
        else:
            raise ExtractorError("Can't find Pin data")

        return {
            "id": video_id,
            "title": title,
            "description": self._og_search_description(webpage),
            "uploader": uploader,
            "url": video_url,
            "ext": "mp4",
            "manifest_url": video_url,
            "thumbnail": video_thumb,
        }

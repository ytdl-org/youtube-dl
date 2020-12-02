# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class VRSumoIE(InfoExtractor):
    _VALID_URL = r"https?://(?:www\.)?vrsumo\.com/(?P<category>[A-Za-z0-9\-]+)/(?P<id>[A-Za-z0-9\-]+).html"
    _TEST = {
        "url": "https://vrsumo.com/full-vr-video/deep-teen-anal-zoe-dolls-petite-body-takes-the-whole-9-inches-3490.html",
        "md5": "a200337879b06f0b44c236feaffa8ae3",
        "info_dict": {
            "id": "deep-teen-anal-zoe-dolls-petite-body-takes-the-whole-9-inches-3490",
            "category": "full-vr-video",
            "ext": "mp4",
            "title": "Deep Teen Anal: Zoe Doll's Petite Body Takes the Whole 9 Inches",
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_category = re.match(self._VALID_URL, url).group("category")
        webpage = self._download_webpage(url, video_id)

        # get the video sources, sort formats
        sources = re.findall(
            r"<source src=\"(?P<url>.*)\" type=\"video/(?P<ext>[a-z0-9]+)\" quality=\"(?P<quality>[A-Za-z0-9 ]+)\" />",
            webpage,
        )
        QUALITIES_SORTED = {
            "All Devices": "1280x640",
            "Mobile Low": "1920x960",
            "Mobile High": "2880x1440",
            "Gear VR": "2880x1440",
            "Oculus 4K": "2880x1440",
        }
        formats = []
        for name, resolution in QUALITIES_SORTED.items():
            for url, ext, quality in sources:
                if name == quality:
                    formats.append(
                        {
                            "url": url,
                            "ext": ext,
                            "format_id": quality,
                            "resolution": QUALITIES_SORTED[quality],
                        }
                    )

        title = self._html_search_regex(
            r"<meta property=\"og:title\" content=\"(.*)\" >", webpage, "title"
        )
        return {
            "id": video_id,
            "category": video_category,
            "title": title,
            "ext": ext,
            "url": url,
            "formats": formats,
        }

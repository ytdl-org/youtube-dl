from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BaddieHubIE(InfoExtractor):
    _VALID_URL = r"https?://(?:www\.)?baddiehub\.com/\?p=(?P<id>[\w\d]+)"
    _TESTS = [
        {
            "url": "https://baddiehub.com/?p=11436",
            "only_matching": True,
        },
        {
            "url": "https://baddiehub.com/?p=11436",
            "md5": "a6ade8a7463326da6fa5cb028290f106",
            "info_dict": {
                "id": "11436",
                "ext": "mp4",
                "title": "Egypt",
                "uploader": "BaddieHub",
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group("id") or mobj.group("name")

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r"<title>(.+?)</title>", webpage, "title")

        content_url = self._html_search_meta('contentURL', webpage)

        author = self._html_search_meta('author', webpage) or "BaddieHub"

        info_dict = {}
        info_dict.update(
            {
                "formats": [
                    {
                        "url": content_url,
                        "ext": "mp4",
                    }
                ],
            }
        )

        info_dict.update(
            {
                "id": video_id,
                "title": title.replace(" – BaddieHub", ""),
                "uploader": author,
            }
        )

        return info_dict

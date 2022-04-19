from __future__ import unicode_literals

import re
from urllib import parse as compat_urlparse

from .common import InfoExtractor
from .commonprotocols import RtmpIE
from .youtube import YoutubeIE
from ..utils import (
    determine_ext,
)


class PornTrexIE(InfoExtractor):
    _VALID_URL = (
        r"https?://(?:www\.)?porntrex\.com/video/(?P<id>[^/?#&.]+)/(?P<name>.*$)"
    )
    _TESTS = [
        {
            "url": "https://www.porntrex.com/video/319817/sunny-leone-2",
            "only_matching": True,
        },
        {
            "url": "https://www.porntrex.com/video/319817/sunny-leone-2",
            "md5": "643ceb579a1ec4f0cf759d4af76d5e83",
            "info_dict": {
                "id": "319817",
                "ext": "mp4",
                "title": "Sunny Leone-Nothing beats a bath to relax",
                "uploader": "www.porntrex.com"
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group("id") or mobj.group("name")

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r"<title>(.+?)</title>", webpage, "title")

        formats = []

        def check_video(vurl):
            if YoutubeIE.suitable(vurl):
                return True
            if RtmpIE.suitable(vurl):
                return True
            vpath = compat_urlparse.urlparse(vurl).path
            vext = determine_ext(vpath)
            return "." in vpath and vext not in (
                "swf",
                "png",
                "jpg",
                "srt",
                "sbv",
                "sub",
                "vtt",
                "ttml",
                "js",
                "xml",
            )

        def filter_video(urls):
            return list(filter(check_video, urls))

        def search_version(reg, page):
            return re.findall(reg, page)

        def get_video_by_regex(reg, page):
            result = filter_video(search_version(reg, page))
            return result.pop() if result else ""

        def get_quality_by_regex(reg, page):
            result = search_version(reg, page)
            return result.pop() if result else ""

        def append_format(f, format_id, vid):
            if format_id and vid:

                height = 0
                if format_id:
                    if len(format_id) == 7 or len(format_id) == 8:
                        format_id = format_id[0:-3]
                        height = int(format_id[:-1])
                    elif len(format_id) == 4:
                        height = int(format_id[:-1])

                draft = {
                    "url": vid,
                    "format_id": format_id,
                    "ext": "mp4",
                }
                if height:
                    draft["height"] = height
                f.append(draft)

        append_format(
            formats,
            get_quality_by_regex(r"(?<=video_url_text: ')[^']+", webpage),
            get_video_by_regex(r"(?<=video_url: ')[^']+", webpage),
        )
        append_format(
            formats,
            get_quality_by_regex(r"(?<=video_alt_url_text: ')[^']+", webpage),
            get_video_by_regex(r"(?<=video_alt_url: ')[^']+", webpage),
        )
        for i in range(2, 8):
            append_format(
                formats,
                get_quality_by_regex(
                    r"(?<=video_alt_url{}_text: ')[^']+".format(i), webpage
                ),
                get_video_by_regex(r"(?<=video_alt_url{}: ')[^']+".format(i), webpage),
            )

        info_dict = {}
        info_dict.update(
            {
                "formats": formats,
            }
        )

        info_dict.update(
            {
                "id": video_id,
                "title": title,
                "uploader": self._search_regex(r"^(?:https?://)?([^/]*)/.*", url, "video uploader", default="www.porntrex.com"),
            }
        )

        return info_dict

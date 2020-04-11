# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class FiteTVIE(InfoExtractor):
    _VALID_URL = r"https?://(?:www\.)?fite\.tv/watch/(?:.+)/(?P<id>.+)/"
    _TESTS = [
        {
            "url": "https://www.fite.tv/watch/all-out-press-conference-weigh-ins/2ozok/",
            "md5": "60986200ae3ed52bfb990611583e0d03",
            "info_dict": {
                "id": "2ozok",
                "ext": "mp4",
                "title": "ALL OUT Press Conference & Weigh In",
                "description": "Official Free Replay: ✓ All Elite Wrestling ✓ Pro Wrestling, Events, Press Conferences ✓ LIVE Aug 29, 8PM ET/5PM PT ✓ Jenn Decker ✓ Hyatt Regency Schaumburg ✓ 1800 E Golf Rd, Schaumburg, IL 60173, USA ✓ You must watch ALL OUT Press Conference & Weigh Ins hosted by Jenn Decker!",
                "thumbnail": r"re:^https?://.*\.jpg$",
            },
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_ld = self._parse_json(
            self._search_regex(
                r'(?s)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json_ld>[^<]+VideoObject[^<]+)</script>',
                webpage,
                "json_ld",
                group="json_ld",
            ),
            video_id,
        )

        info_dict = self._json_ld(json_ld, video_id)

        formats = self._extract_m3u8_formats(
            "https://www.fite.tv/embed/play/%s.m3u8?" % video_id, video_id, "mp4"
        )

        self._sort_formats(formats)

        title = info_dict.get("title") or self._og_search_title(webpage)
        description = info_dict.get("description") or self._og_search_description(webpage)
        thumbnail = info_dict.get("thumbnail") or self._og_search_thumbnail(webpage)

        return {
            "id": video_id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "formats": formats,
        }

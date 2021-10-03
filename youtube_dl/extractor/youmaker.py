import calendar
import re
from datetime import datetime

from .common import InfoExtractor
from .. import utils


class YouMakerIE(InfoExtractor):
    _VALID_URL = r"""(?x)
                    https?://(?:www\.)?youmaker\.com/
                    (?:v|video|embed)/
                    (?P<id>[0-9a-zA-Z-]+)
                    """

    _TESTS = [
        {
            "url": "https://www.youmaker.com/v/Dnnrq0lw8062",
            "info_dict": {
                "id": "77c92592-57fa-4bfc-a5da-79e965667001",
                "ext": "mp4",
                "title": "Althistoriker Dr. David Engels im Interview: „Das ist der echte Untergang des Abendlandes“",
                "description": "Im Interview mit Epoch Times führt der belgische Althistoriker Dr. David Engels aus, "
                "wie sich der Zerfall der europäischen Staatengemeinschaft im Zuge der Corona-Krise "
                "zugespitzt hat, und zeichnet Parallelen zu den letzten Atemzügen der spätrömischen "
                "Republik. , , Der Artikel zu dem Interview folgt in Kürze "
                "hier: https://www.epochtimes.de/wissen/gesellschaft/"
                "das-ist-der-echte-untergang-des-abendlandes-a3613553.html - Youmaker",
                "duration": 3507,
                "upload_date": "20211001",
                "timestamp": 1633046400,
            },
            "params": {
                "skip_download": True,
                "nocheckcertificate": True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            "https://youmaker.com/video/%s" % video_id, video_id
        )

        info = self._parse_json(
            self._search_regex(
                (
                    r'<script\s+type="application/ld\+json">s*'
                    r"(?P<json>{[^}]+})"
                    r"\s*</script>"
                ),
                webpage,
                "json_info",
                default="{}",
                group="json",
            ),
            video_id,
        )

        thumbnail_urls = info.get("thumbnailUrl", [])
        if not thumbnail_urls:
            raise utils.ExtractorError("Resource not available", expected=False)

        asset_base = thumbnail_urls[0].rsplit("/", maxsplit=1)[0]
        match = re.match(r".*/assets/(\d\d\d\d)/(\d\d\d\d)/([^/]+)$", asset_base)
        if match:
            upload_date = "".join(match.groups()[0:2])
            dt = datetime.strptime(upload_date, "%Y%m%d")
            timestamp = calendar.timegm(dt.timetuple())
            video_id = match.groups()[2]
        else:
            upload_date = utils.unified_strdate(info["uploadDate"])
            timestamp = utils.parse_iso8601(info["uploadDate"])

        formats = self._extract_m3u8_formats(
            "/".join((asset_base, "playlist.m3u8")),
            video_id,
            ext="mp4",
        )
        parts_d = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(\d+)S", info["duration"]).groups()
        duration = sum((int(n) * l for n, l in zip(parts_d, (3600, 60, 1)) if n))
        for item in formats:
            item["format_id"] = "hls-%dp" % item["height"]
            item["filesize_approx"] = 128 * item["tbr"] * duration

        ret_info = {
            "id": video_id,
            "formats": formats,
            "title": info["name"],
            "description": info["description"],
            "timestamp": timestamp,
            "upload_date": upload_date,
            "duration": duration,
            "channel": info.get("author"),
            "thumbnails": [{"url": url} for url in thumbnail_urls],
            "view_count": utils.int_or_none(info.get("interactionCount")),
        }

        return ret_info

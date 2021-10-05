# coding: utf-8
from __future__ import unicode_literals

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
            "url": "http://www.youmaker.com/v/71b5d2c5-31b6-43b8-8475-1dcb5e10dfb0",
            "info_dict": {
                "id": "71b5d2c5-31b6-43b8-8475-1dcb5e10dfb0",
                "ext": "mp4",
                "title": "Как сшить шапочку из трикотажа. Плоский шов двойной иглой.",
                "description": r"re:(?s)^Привет друзья!\n\nВ этом видео я .* представлена www\.iksonmusic\.com$",
                "thumbnail": r"re:^https?://.*\.(?:jpg|png)$",
                "duration": 358,
                "upload_date": "20190614",
                "uploader": "user_318f21e00e1f8a6b414f20a654d0f4fc7d2053bc",
                "timestamp": 1560554895,
                "channel": "Sewing Ideas",
                "channel_id": "40ca79f7-8b21-477f-adba-7d0f81e5b5fd",
                "channel_url": r"re:https?://www.youmaker.com/channel/40ca79f7-8b21-477f-adba-7d0f81e5b5fd",
                "tags": [
                    "как сшить детскую шапочку из трикотажа",
                    "как шить двойной иглой трикотаж",
                ],
            },
            "params": {
                "skip_download": True,
            },
        },
    ]

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        super(YouMakerIE, self).__init__(downloader=downloader)
        self.__protocol = "https"

    def _fix_url(self, url):
        if url.startswith("//"):
            return "%s:%s" % (self.__protocol, url)
        return url

    @property
    def _base_url(self):
        return self._fix_url("//www.youmaker.com")

    @property
    def _api_url(self):
        return "%s/v1/api" % self._base_url

    @property
    def _asset_url(self):
        # as this url might change in the future
        # it needs to be extracted from some js magic...
        return self._fix_url("//vs.youmaker.com/assets")

    def _get_subtitles(self, system_id=None):
        subtitles = {}

        if system_id is None:
            return subtitles

        info = self._download_json(
            "%s/video/subtitle?systemid=%s" % (self._api_url, system_id),
            system_id,
        )

        if info.get("status") != "ok":
            return subtitles

        for item in info.get("data", []):
            subtitles.setdefault(item["language_code"], []).append(
                {"url": "%s/%s" % (self._asset_url, item["url"])}
            )
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if url.startswith("http://"):
            self.__protocol = "http"
        info = self._download_json(
            "%s/video/metadata/%s" % (self._api_url, video_id), video_id
        )

        status = info.get("status", "something went wrong")
        if status != "ok":
            raise utils.ExtractorError(status, expected=True)

        info = info["data"]
        info["tags"] = [
            tag.strip() for tag in info.get("tag", "").strip("[]").split(",") if tag
        ]
        info["channel_url"] = (
            "%s/channel/%s" % (self._base_url, info["channel_uid"])
            if "channel_uid" in info
            else None
        )
        video_info = info.get("data", {})
        duration = video_info.get("duration")
        formats = []
        playlist = video_info.get("videoAssets", {}).get("Stream")

        if playlist:
            formats.extend(
                self._extract_m3u8_formats(
                    self._fix_url(playlist),
                    video_id,
                    ext="mp4",
                )
            )

        if formats:
            self._sort_formats(formats)
            for item in formats:
                item["format_id"] = "hls-%dp" % item["height"]
                if duration and item.get("tbr"):
                    item["filesize_approx"] = 128 * item["tbr"] * duration

        return {
            "id": info["video_uid"],
            "title": info["title"],
            "description": info["description"],
            "formats": formats,
            "timestamp": utils.parse_iso8601(info["uploaded_at"]),
            "upload_date": utils.unified_strdate(info["uploaded_at"]),
            "uploader": info.get("uploaded_by"),
            "duration": duration,
            "tags": info["tags"],
            "channel": info.get("channel_name"),
            "channel_id": info.get("channel_uid"),
            "channel_url": info["channel_url"],
            "thumbnail": info.get("thumbmail_path"),
            "view_count": info.get("click"),
            "subtitles": self.extract_subtitles(info.get("system_id")),
        }

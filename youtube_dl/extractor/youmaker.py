# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlencode
from ..utils import parse_iso8601, unified_strdate, ExtractorError


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
                "categories": ["Life", "How-to & DIY"],
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
        self.__video_id = None
        self.__cache = {}

    def _set_id_and_protocol(self, url):
        self.__video_id = self._match_id(url)
        if url.startswith("http://"):
            self.__protocol = "http"

    def _fix_url(self, url):
        if url.startswith("//"):
            return "%s:%s" % (self.__protocol, url)
        return url

    @property
    def _base_url(self):
        return self._fix_url("//www.youmaker.com")

    @property
    def _asset_url(self):
        # as this url might change in the future
        # it needs to be extracted from some js magic...
        return self._fix_url("//vs.youmaker.com/assets")

    def _api(self, path, cache=False, **kwargs):
        """
        call the YouMaker JSON API and return the data

        path:       API endpoint
        **kwargs:   parameters passed to _download_json()
        """
        key = hash((path, compat_urllib_parse_urlencode(kwargs.get("query", {}))))
        if cache and key in self.__cache:
            return self.__cache[key]

        url = "%s/v1/api/%s" % (self._base_url, path)
        info = self._download_json(url, self.__video_id, **kwargs)
        status = info.get("status", "something went wrong")
        data = info.get("data")
        if status != "ok" or data is None:
            raise ExtractorError(status, expected=True)

        if cache:
            self.__cache[key] = data

        return data

    def _categories_by_id(self, cid):
        category_map = self.__cache.get("category_map")
        if category_map is None:
            category_list = self._api(
                "video/category/list", note="Downloading categories"
            )
            category_map = {item["category_id"]: item for item in category_list}
            self.__cache["category_map"] = category_map

        categories = []
        while True:
            item = category_map.get(cid)
            if item is None or item["category_name"] in categories:
                break
            categories.insert(0, item["category_name"])
            cid = item["parent_category_id"]

        return categories

    def _get_subtitles(self, system_id):
        try:
            assert system_id is not None
            subs_list = self._api(
                "video/subtitle",
                note="checking for subtitles",
                query={"systemid": system_id},
            )
        except (AssertionError, ExtractorError):
            return {}

        subtitles = {}
        for item in subs_list:
            subtitles.setdefault(item["language_code"], []).append(
                {"url": "%s/%s" % (self._asset_url, item["url"])}
            )

        return subtitles

    def _real_extract(self, url):
        self._set_id_and_protocol(url)

        info = self._api(
            "video/metadata/%s" % self.__video_id, note="Downloading video metadata"
        )

        # check some dictionary keys so it's safe to use them
        mandatory_keys = {"video_uid", "title", "data"}
        missing_keys = mandatory_keys - set(info.keys())
        if missing_keys:
            raise ExtractorError("Missing video metadata: %s" % ", ".join(missing_keys))

        tag_str = info.get("tag")
        if tag_str:
            tags = [tag.strip() for tag in tag_str.strip("[]").split(",")]
        else:
            tags = None

        channel_url = (
            "%s/channel/%s" % (self._base_url, info["channel_uid"])
            if "channel_uid" in info
            else None
        )

        video_info = info["data"]  # asserted before
        duration = video_info.get("duration")

        formats = []
        playlist = video_info.get("videoAssets", {}).get("Stream")

        if playlist:
            formats.extend(
                self._extract_m3u8_formats(
                    self._fix_url(playlist),
                    self.__video_id,
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
            "id": info["video_uid"],  # asserted before
            "title": info["title"],  # asserted before
            "description": info.get("description"),
            "formats": formats,
            "timestamp": parse_iso8601(info.get("uploaded_at")),
            "upload_date": unified_strdate(info.get("uploaded_at")),
            "uploader": info.get("uploaded_by"),
            "duration": duration,
            "categories": self._categories_by_id(info.get("category_id")),
            "tags": tags,
            "channel": info.get("channel_name"),
            "channel_id": info.get("channel_uid"),
            "channel_url": channel_url,
            "thumbnail": info.get("thumbmail_path"),
            "view_count": info.get("click"),
            "subtitles": self.extract_subtitles(info.get("system_id")),
        }

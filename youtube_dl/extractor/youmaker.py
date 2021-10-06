# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
    compat_urlparse,
)
from ..utils import parse_iso8601, unified_strdate, ExtractorError


class YouMakerIE(InfoExtractor):
    _VALID_URL = r"""(?x)
                    (?P<protocol>https?)://(?:www\.)?youmaker\.com/
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
        self.__cache = {}

    @classmethod
    def _match_url(cls, url):
        if "_VALID_URL_RE" not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        match = cls._VALID_URL_RE.match(url)
        assert match
        return match.groupdict()

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

    def _live_url(self, video_id):
        return self._fix_url("//live.youmaker.com/%s/playlist.m3u8" % video_id)

    def _api(self, uid, path, cache=False, **kwargs):
        """
        call the YouMaker JSON API and return the data object
        otherwise raises ExtractorError

        path:       API endpoint
        cache:      if True, use cached result on multiple calls
        **kwargs:   parameters passed to _download_json()
        """
        key = hash((path, compat_urllib_parse_urlencode(kwargs.get("query", {}))))
        if cache and key in self.__cache:
            return self.__cache[key]

        url = "%s/v1/api/%s" % (self._base_url, path)
        info = self._download_json(url, uid, **kwargs)
        status = info.get("status", "something went wrong")
        data = info.get("data")
        if status != "ok" or data is None:
            raise ExtractorError(status, video_id=uid, expected=True)

        if cache:
            self.__cache[key] = data

        return data

    def _categories_by_id(self, cid):
        category_map = self.__cache.get("category_map")
        if category_map is None:
            category_list = self._api(
                None, "video/category/list", note="Downloading categories"
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
                system_id,
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

    def _video_entry(self, info):
        # check some dictionary keys so it's safe to use them
        mandatory_keys = {"video_uid", "title", "data"}
        missing_keys = mandatory_keys - set(info.keys())
        if missing_keys:
            raise ExtractorError(
                "Missing video metadata: %s" % ", ".join(missing_keys),
                video_id=self.ie_key(),
            )

        video_uid = info["video_uid"]
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

        if info.get("live") and info.get("live_status") == "start":
            is_live = True
            playlist = self._live_url(video_uid)
        else:
            is_live = False
            playlist = video_info.get("videoAssets", {}).get("Stream")

        if playlist:
            formats.extend(
                self._extract_m3u8_formats(
                    self._fix_url(playlist),
                    video_uid,
                    ext="mp4",
                    fatal=False,
                    errnote="%s (playlist.m3u8)" % video_uid,
                )
            )

        if not formats:
            raise ExtractorError(
                "No video formats found!", video_id=video_uid, expected=True
            )

        self._sort_formats(formats)
        for item in formats:
            if "height" not in item:
                continue
            item["format_id"] = "hls-%dp" % item["height"]
            if duration and item.get("tbr"):
                item["filesize_approx"] = 128 * item["tbr"] * duration

        return {
            "id": video_uid,
            "title": info["title"],  # asserted before
            "description": info.get("description"),
            "formats": formats,
            "is_live": is_live,
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

    def _real_extract(self, url):
        url_info = self._match_url(url)
        self.__protocol = url_info["protocol"]
        info = self._api(
            url_info["id"],
            "video/metadata/%s" % url_info["id"],
            note="Downloading video metadata",
        )

        return self._video_entry(info)


class YouMakerPlaylistIE(YouMakerIE):
    _VALID_URL = r"""(?x)
                    https?://(?:www\.)?youmaker\.com/
                    (?:channel|playlist)/(?P<id>[0-9a-zA-Z-]+)
                    """
    _TESTS = [
        {
            # all videos from channel
            "url": "http://www.youmaker.com/channel/f06b2e8d-219e-4069-9003-df343ac5fcf3",
            "info_dict": {
                "id": "f06b2e8d-219e-4069-9003-df343ac5fcf3",
                "title": "YoYo Cello",
                "description": "Connect the World Through Music. \nConnect Our Hearts with Music.",
            },
            "playlist_mincount": 30,
            "params": {
                "nocheckcertificate": True,
            },
        },
        {
            # all videos from channel playlist
            "url": "https://www.youmaker.com/channel/f8d585f8-2ff7-4c3c-b1ea-a78d77640d54/"
            "playlists/f99a120c-7a5e-47b2-9235-3817d1c12662",
            "info_dict": {
                "id": "f99a120c-7a5e-47b2-9235-3817d1c12662",
                "title": "Mini Cakes",
            },
            "playlist_mincount": 9,
            "params": {
                "nocheckcertificate": True,
            },
        },
    ]

    def _channel_entries(self, _channel_uid, api_path, **api_params):
        request_limit = 50
        offset = int(api_params.get("offset", 0))

        while True:
            api_params.update({"offset": offset, "limit": request_limit})
            info = self._api(
                _channel_uid,
                path=api_path,
                query=api_params,
                note="Downloading video metadata (%d-%d)"
                % (offset, offset + request_limit),
            )
            offset += request_limit
            for item in info:
                try:
                    entry = self._video_entry(item)
                except ExtractorError as exc:
                    self.report_warning(str(exc))
                    continue
                yield entry

            if len(info) < request_limit:
                break

    def _playlist_entries(self, playlist_uid, request_limit=50):
        video_extractor = YouMakerIE(downloader=self._downloader)
        offset = 0

        while True:
            info = self._api(
                playlist_uid,
                path="playlist/video",
                query={
                    "playlist_uid": playlist_uid,
                    "offset": offset,
                    "limit": request_limit,
                },
                note="Downloading video metadata (%d-%d)"
                % (offset, offset + request_limit),
            )
            offset += request_limit
            for item in info:
                url = "%s/video/%s" % (self._base_url, item["video_uid"])
                try:
                    entry = video_extractor._real_extract(url)
                except ExtractorError as exc:
                    self.report_warning(str(exc))
                    continue
                yield entry

            if len(info) < request_limit:
                break

    def _real_extract(self, url):
        parsed_url = compat_urllib_parse_urlparse(url)
        self.__protocol = parsed_url.scheme

        playlist_matches = (
            (
                "playlist",
                r"(/channel/[a-zA-z0-9-]+)?/playlists?/(?P<id>[a-zA-z0-9-]+).*",
            ),
            ("hottest", r"/channel/(?P<id>[a-zA-z0-9-]+)/hottest(/.*)?"),
            ("channel", r"/channel/(?P<id>[a-zA-z0-9-]+)(/.*)?"),
        )

        for name, regex in playlist_matches:
            match = re.match(regex, parsed_url.path)
            if not match:
                continue
            break
        else:
            raise ExtractorError(
                "unsupported url", video_id=self.ie_key(), expected=True
            )

        uid = match.group("id")
        if name == "playlist":
            info = self._api(
                uid,
                "playlist/%s" % uid,
                note="Downloading playlist metadata",
            )
            return self.playlist_result(
                self._playlist_entries(
                    info["playlist_uid"],
                ),
                playlist_id=info["playlist_uid"],
                playlist_title=info.get("name"),
                playlist_description=None,
            )

        # otherwise provide all channel videos
        info = self._api(
            uid,
            "video/channel/metadata/%s" % uid,
            note="Downloading channel metadata",
        )
        uid = info["channel_uid"]

        if name == "hottest":
            return self.playlist_result(
                self._channel_entries(uid, api_path="video/hottest", channel_uid=uid),
                playlist_id=uid,
                playlist_title=info.get("name"),
                playlist_description=info.get("description"),
            )

        query = dict(compat_urlparse.parse_qsl(parsed_url.query))
        if "keywords" in query:
            # filter by keywords
            api_path = "video/search"
            params = {
                "keywords": query["keywords"],
                "channel_uid": uid,
                "order": query.get("order", 1),
            }
        else:
            # return all channel entries
            api_path = "video/channel/%s" % uid
            params = {"offset": query.get("offset", 0)}

        return self.playlist_result(
            self._channel_entries(uid, api_path=api_path, **params),
            playlist_id=info["channel_uid"],
            playlist_title=info.get("name"),
            playlist_description=info.get("description"),
        )

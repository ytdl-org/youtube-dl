# coding: utf-8
from __future__ import unicode_literals

import os.path
import re
from operator import itemgetter

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
    compat_urlparse,
    compat_str,
)
from ..utils import parse_iso8601, unified_strdate, ExtractorError, try_get


class ParsedURL(object):
    """
    This class provides a unified interface for urlparse(),
    parse_qsl() and regular expression groups
    """

    def __init__(self, url, regex=None):
        self._match = None
        self._groups = {}
        self._query = query = {}
        self._parts = parts = compat_urllib_parse_urlparse(url)

        for key, value in compat_urlparse.parse_qsl(parts.query):
            query[key] = int(value) if value.isdigit() else value

        if regex:
            self._match = re.match(regex, url)
            assert self._match, "regex does not match url"

    def __getattr__(self, item):
        """
        forward the attributes from urlparse.ParsedResult
        thus providing scheme, netloc, url, params, fragment

        note that .query is shadowed by a different method
        """
        return getattr(self._parts, item)

    def query(self, key=None, default=None):
        if key is None:
            return dict(self._query)

        return self._query.get(key, default)

    def regex_group(self, key=None):
        assert self._match, "no regex provided"
        if key is None:
            return self._match.groupdict()

        return self._match.group(key)


class YouMakerIE(InfoExtractor):
    _VALID_URL = r"""(?x)
                    https?://(?:[a-z][a-z0-9]+\.)?youmaker\.com/
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

    def _call_api(self, uid, path, cache=False, what="JSON metadata", **kwargs):
        """
        call the YouMaker JSON API and return a valid data object

        path:       API endpoint
        cache:      if True, use cached result on multiple calls
        what:       query description
        fatal:      if True might raise ExtractorError otherwise warn and return None
        **kwargs:   parameters passed to _download_json()
        """
        key = hash((path, compat_urllib_parse_urlencode(kwargs.get("query", {}))))
        if cache and key in self.__cache:
            return self.__cache[key]

        url = "%s/v1/api/%s" % (self._base_url, path)
        kwargs.setdefault("note", "Downloading %s" % what)
        kwargs.setdefault("errnote", "Failed to download %s" % what)
        info = self._download_json(url, uid, **kwargs)

        # soft error already reported
        if info is False:
            return None

        status = try_get(info, itemgetter("status"), compat_str)
        data = try_get(info, itemgetter("data"), (list, dict))

        if status != "ok":
            msg = "%s - %s" % (what, status or "Bad JSON response")
            if kwargs.get("fatal", True) or status is None:
                raise ExtractorError(
                    msg, video_id=uid, expected=isinstance(status, compat_str)
                )
            self.report_warning(msg, video_id=uid)

        if cache:
            self.__cache[key] = data

        return data

    @property
    def _category_map(self):
        category_map = self.__cache.get("category_map")
        if category_map is not None:
            return category_map
        category_list = (
            self._call_api(
                None,
                "video/category/list",
                what="categories",
                fatal=False,
            )
            or ()
        )
        category_map = {item["category_id"]: item for item in category_list}
        self.__cache["category_map"] = category_map
        return category_map

    def _categories_by_id(self, cid):
        categories = []
        if cid is None:
            return categories

        category_map = self._category_map
        while True:
            item = category_map.get(cid)
            if item is None or item["category_name"] in categories:
                break
            categories.insert(0, item["category_name"])
            cid = item["parent_category_id"]

        return categories

    def _get_subtitles(self, system_id):
        if system_id is None:
            return {}

        subs_list = (
            self._call_api(
                system_id,
                "video/subtitle",
                what="subtitle info",
                query={"systemid": system_id},
                fatal=False,
            )
            or {}
        )

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
            playlist_name = os.path.basename(playlist)
            formats.extend(
                self._extract_m3u8_formats(
                    self._fix_url(playlist),
                    video_uid,
                    ext="mp4",
                    fatal=False,
                    note="Downloading %s" % playlist_name,
                    errnote="%s (%s)" % (video_uid, playlist_name),
                )
            )

        if not formats:
            # as there are some videos on the platform with missing playlist
            # expected is set True
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
        parsed_url = ParsedURL(url, regex=self._VALID_URL)
        self.__protocol = parsed_url.scheme
        uid = parsed_url.regex_group("id")

        info = self._call_api(
            uid,
            "video/metadata/%s" % uid,
            what="video metadata",
        )

        return self._video_entry(info)


class YouMakerPlaylistIE(YouMakerIE):
    _VALID_URL = r"""(?x)
                    https?://(?:[a-z][a-z0-9]+\.)?youmaker\.com/
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
        {
            # check using search keywords, we take something that does not match any videos
            "url": "https://www.youmaker.com/channel/40ca79f7-8b21-477f-adba-7d0f81e5b5fd?channel_keyword=nomatch",
            "info_dict": {
                "id": "40ca79f7-8b21-477f-adba-7d0f81e5b5fd",
                "title": "Sewing Ideas",
                "description": r"re:Добро пожаловать на канал Швейные Идеи! .*",
            },
            "playlist_count": 0,
            "params": {
                "nocheckcertificate": True,
            },
        },
    ]

    def _channel_entries(self, _channel_uid, api_path, **api_params):
        request_limit = 50
        offset = api_params.get("offset", 0)

        while True:
            api_params.update({"offset": offset, "limit": request_limit})
            info = self._call_api(
                _channel_uid,
                path=api_path,
                what="video metadata (%d-%d)" % (offset, offset + request_limit),
                query=api_params,
            )
            offset += request_limit
            for item in info:
                try:
                    entry = self._video_entry(item)
                except ExtractorError as exc:
                    self.report_warning(exc)
                    continue
                yield entry

            if len(info) < request_limit:
                break

    def _playlist_entries(self, playlist_uid, request_limit=50):
        video_extractor = YouMakerIE(downloader=self._downloader)
        offset = 0

        while True:
            info = self._call_api(
                playlist_uid,
                path="playlist/video",
                what="video metadata (%d-%d)" % (offset, offset + request_limit),
                query={
                    "playlist_uid": playlist_uid,
                    "offset": offset,
                    "limit": request_limit,
                },
            )
            offset += request_limit
            for item in info:
                url = "%s/video/%s" % (self._base_url, item["video_uid"])
                try:
                    entry = video_extractor._real_extract(url)
                except ExtractorError as exc:
                    self.report_warning(exc)
                    continue
                yield entry

            if len(info) < request_limit:
                break

    def _real_extract(self, url):
        parsed_url = ParsedURL(url)
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
            info = self._call_api(
                uid,
                "playlist/%s" % uid,
                what="playlist metadata",
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
        info = self._call_api(
            uid,
            "video/channel/metadata/%s" % uid,
            what="channel metadata",
        )
        uid = info["channel_uid"]

        if name == "hottest":
            return self.playlist_result(
                self._channel_entries(uid, api_path="video/hottest", channel_uid=uid),
                playlist_id=uid,
                playlist_title=info.get("name"),
                playlist_description=info.get("description"),
            )

        keywords = parsed_url.query("channel_keyword")
        if keywords:
            # filter by keywords
            api_path = "video/search"
            params = {
                "keywords": keywords,
                "channel_uid": uid,
                "order": parsed_url.query("order", 1),
            }
        else:
            # return all channel entries
            api_path = "video/channel/%s" % uid
            params = {"offset": parsed_url.query("offset", 0)}

        return self.playlist_result(
            self._channel_entries(uid, api_path=api_path, **params),
            playlist_id=info["channel_uid"],
            playlist_title=info.get("name"),
            playlist_description=info.get("description"),
        )

# coding: utf-8
from __future__ import unicode_literals

import os.path
import re
from collections import Sequence
from operator import itemgetter

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
    compat_str,
)
from ..utils import parse_iso8601, ExtractorError, try_get, OnDemandPagedList


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


class YoumakerIE(InfoExtractor):
    _VALID_URL = r"""(?x)
                    https?://(?:[a-z][a-z0-9]+\.)?youmaker\.com/
                    (?:v|video|embed|channel|playlist)/
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
    REQUEST_LIMIT = 50

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        super(YoumakerIE, self).__init__(downloader=downloader)
        self._protocol = "https"
        self._category_map = None
        self._cache = {}

    @staticmethod
    def _extract_url(webpage):
        match = re.search(
            r'<iframe[^>]+src="(?P<url>https?://(?:www\.)?youmaker\.com/embed/[0-9a-zA-Z-]+)[^"]*"',
            webpage,
        )
        return match.group("url") if match else None

    def _fix_url(self, url):
        if url.startswith("//"):
            return "%s:%s" % (self._protocol, url)
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

    def _call_api(self, uid, path, what="JSON metadata", fatal=True, **kwargs):
        """
        call the YouMaker JSON API and return a valid data object

        path:       API endpoint
        what:       query description
        fatal:      if True might raise ExtractorError otherwise warn and return None
        **kwargs:   parameters passed to _download_json()
        """
        url = "%s/v1/api/%s" % (self._base_url, path)
        kwargs.setdefault("note", "Downloading %s" % what)
        kwargs.setdefault("errnote", "Failed to download %s" % what)
        info = self._download_json(url, uid, fatal=fatal, **kwargs)

        # soft error already reported
        if info is False:
            return None

        status = try_get(info, itemgetter("status"), compat_str)
        data = try_get(info, itemgetter("data"), (list, dict))

        if status != "ok":
            msg = "%s - %s" % (what, status or "Bad JSON response")
            if fatal or status is None:
                raise ExtractorError(
                    msg, video_id=uid, expected=isinstance(status, compat_str)
                )
            self.report_warning(msg, video_id=uid)

        return data

    @property
    def _categories(self):
        if self._category_map is None:
            category_list = (
                self._call_api(
                    None,
                    "video/category/list",
                    what="categories",
                    fatal=False,
                )
                or ()
            )
            self._category_map = {item["category_id"]: item for item in category_list}
        return self._category_map

    def _categories_by_id(self, cid):
        categories = []
        if cid is None:
            return categories

        while True:
            item = self._categories.get(cid)
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
            or ()
        )

        subtitles = {}
        for item in subs_list:
            subtitles.setdefault(item["language_code"], []).append(
                {"url": "%s/%s" % (self._asset_url, item["url"])}
            )

        return subtitles

    def _video_entry_by_metadata(self, info):
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
                    entry_protocol="m3u8" if is_live else "m3u8_native",
                    note="Downloading %s" % playlist_name,
                    errnote="%s (%s)" % (video_uid, playlist_name),
                    fatal=False,
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
            height = try_get(item, itemgetter("height"), int)
            if height:
                item["format_id"] = "%dp" % item["height"]
            tbr = try_get(item, itemgetter("tbr"), (int, float))
            if duration and tbr:
                item["filesize_approx"] = 128 * tbr * duration

        return {
            "id": video_uid,
            "title": info["title"],  # asserted before
            "description": info.get("description"),
            "formats": formats,
            "is_live": is_live,
            "timestamp": parse_iso8601(info.get("uploaded_at")),
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

    def _video_entry_by_id(self, uid):
        info = self._cache.get(uid) or self._call_api(
            uid,
            "video/metadata/%s" % uid,
            what="video metadata",
        )

        return self._video_entry_by_metadata(info)

    def _paged_playlist_entries(self, uid, page_size=REQUEST_LIMIT):
        def fetch_page(page_number):
            offset = page_number * page_size
            info = self._call_api(
                uid,
                path="playlist/video",
                what="playlist entries %d-%d" % (offset + 1, offset + page_size),
                query={"playlist_uid": uid, "offset": offset, "limit": page_size},
            )
            if not isinstance(info, Sequence):
                raise ExtractorError("Unexpected playlist entries", uid, expected=False)

            for item in info:
                yield self.url_result(
                    "%s/video/%s" % (self._base_url, item["video_uid"]),
                    ie=self.ie_key(),
                    video_id=item["video_uid"],
                    video_title=item["video_title"],
                )

        _ = self._categories  # preload categories
        return OnDemandPagedList(fetch_page, page_size)

    def _paged_channel_entries(self, uid, page_size=REQUEST_LIMIT):
        def fetch_page(page_number):
            offset = page_number * page_size
            info = self._call_api(
                uid,
                path="video/channel/%s" % uid,
                what="channel entries %d-%d" % (offset + 1, offset + page_size),
                query={"offset": offset, "limit": page_size},
            )
            if not isinstance(info, Sequence):
                raise ExtractorError("Unexpected channel entries", uid, expected=False)

            for item in info:
                self._cache[item["video_uid"]] = item
                yield self.url_result(
                    "%s/video/%s" % (self._base_url, item["video_uid"]),
                    ie=self.ie_key(),
                    video_id=item["video_uid"],
                    video_title=item["title"],
                )

        _ = self._categories  # preload categories
        return OnDemandPagedList(fetch_page, page_size)

    def _playlist_entries_by_id(self, uid):
        _ = self._categories  # preload categories
        info = self._call_api(
            uid,
            "playlist/%s" % uid,
            what="playlist metadata",
        )
        return self.playlist_result(
            self._paged_playlist_entries(
                info["playlist_uid"],
            ),
            playlist_id=info["playlist_uid"],
            playlist_title=info.get("name"),
            playlist_description=None,
        )

    def _channel_entries_by_id(self, uid):
        _ = self._categories  # preload categories
        info = self._call_api(
            uid,
            path="video/channel/metadata/%s" % uid,
            what="channel metadata",
        )
        return self.playlist_result(
            self._paged_channel_entries(
                info["channel_uid"],
            ),
            playlist_id=info["channel_uid"],
            playlist_title=info.get("name"),
            playlist_description=info.get("description"),
        )

    def _real_extract(self, url):
        parsed_url = ParsedURL(url)
        self._protocol = parsed_url.scheme

        dispatch = (
            (r"/(?:v|video|embed)/(?P<uid>[a-zA-z0-9-]+)", self._video_entry_by_id),
            (
                r"(/channel/[a-zA-z0-9-]+)?/playlists?/(?P<uid>[a-zA-z0-9-]+)",
                self._playlist_entries_by_id,
            ),
            (r"/channel/(?P<uid>[a-zA-z0-9-]+)/?$", self._channel_entries_by_id),
        )

        for regex, func in dispatch:
            match = re.match(regex, parsed_url.path)
            if not match:
                continue
            return func(**match.groupdict())
        else:
            raise ExtractorError("unsupported %s url" % self.ie_key(), expected=True)

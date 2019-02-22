# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_iso8601
from copy import deepcopy
from datetime import datetime


class StreamMeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stream\.me/archive/(?:[0-9a-zA-Z_]+)/(?:[0-9a-zA-Z\-]+?)/(?P<id>[0-9a-zA-Z]+)/?'
    _TESTS = (
        {
            "url": "https://www.stream.me/archive/mistermetokur/fishing-with-trout/GYPX9D6VYk",
            "md5": "e6c92a5f65d5798a6074ae2f0ff4da6b",
            "info_dict": {
                "id": "GYPX9D6VYk",
                "ext": "mp4",
                "title": "Fishing With Trout",
                "description": "Guest: Kraut&Tea",
                "display_id": "fishing-with-trout",
                "release_date": "20190203",
                "timestamp": 1549220944,
                "upload_date": "20190203",
                "age_limit": 13,
                "uploader_id": "MisterMetokur",
                "uploader_url": "https://www.stream.me/mistermetokur",
                "uploader": "MisterMetokur",
                "duration": 4536,
                "categories": ["Fish", ],
                "tags": [],
                "is_live": False,
                "thumbnail": r're:^https?://.*\.jpg$',
            }
        },
        {
            "url": "https://www.stream.me/archive/theralphretort/killstream-tonka-cant-melt-steel-beams/1Y9DeeyBlO",
            "md5": "03b8d9ac4ef5887d7cfccc944b79ae1d",
            "info_dict": {
                "id": "1Y9DeeyBlO",
                "ext": "mp4",
                "title": "#Killstream: Tonka Can't Melt Steel Beams",
                "description": "",
                "display_id": "killstream-tonka-cant-melt-steel-beams",
                "release_date": "20190116",
                "timestamp": 1547639605,
                "upload_date": "20190116",
                "age_limit": 13,
                "uploader_id": "TheRalphRetort",
                "uploader_url": "https://www.stream.me/theralphretort",
                "uploader": "Ralph",
                "duration": 30716,
                "categories": [],
                "tags": ["Killstream", ],
                "is_live": False,
                "thumbnail": r're:^https?://.*\.jpg$',
            }
        },
        {
            "url": "https://www.stream.me/archive/godspeedlive/godspeedlive-gunts-so-weird/rlWxxBjAYv",
            "md5": "2ec90e657f2c5227446bab5d7875d88a",
            "info_dict": {
                "id": "rlWxxBjAYv",
                "ext": "mp4",
                "title": "GodspeedLive, Gunt's so weird",
                "description": "",
                "display_id": "godspeedlive-gunts-so-weird",
                "release_date": "20190215",
                "timestamp": 1550200571,
                "upload_date": "20190215",
                "age_limit": 13,
                "uploader_id": "GodspeedLive",
                "uploader_url": "https://www.stream.me/godspeedlive",
                "uploader": "ゴッドスピードライブ",
                "duration": 2350,
                "categories": [],
                "tags": [],
                "is_live": False,
                "thumbnail": r're:^https?://.*\.jpg$',
            }
        },
    )

    def _real_extract(self, url):
        result = {}
        url_id = self._match_id(url)
        result["id"] = url_id

        webpage = self._download_webpage(url, url_id)
        script_data_raw = self._html_search_regex(
            r'<script>[^{} ><=]+context\s+=\s+([^><]+);\s*</script>',
            webpage,
            'HTML inline JSON data')
        data = self._parse_json(script_data_raw, url_id)
        vod = data["vod"]
        links = vod["_links"]
        stats = vod.get("stats", {}).get("raw", {})
        topics = vod.get("topics", [])
        tags = vod.get("tags", [])
        time_raw = vod.get("whenCreated")
        try:
            result["timestamp"] = int(parse_iso8601(time_raw))
            result["release_date"] \
                = datetime.utcfromtimestamp(result["timestamp"]).strftime("%Y%m%d")
        except (ValueError, KeyError, ):
            pass

        result["url"] = links["hlsmp4"]["href"]
        result["title"] = vod.get("title")
        result["description"] = vod.get("description")
        result["display_id"] = vod.get("titleSlug")
        result["age_limit"] = vod.get("ageRating")
        result["uploader_id"] = vod.get("username")
        if "userSlug" in vod:
            result["uploader_url"] = "https://www.stream.me/" + vod.get("userSlug")
        result["uploader"] = vod.get("displayName")
        result["duration"] = vod.get("duration")
        result["view_count"] = stats.get("views")
        result["like_count"] = stats.get("likes")
        result["dislike_count"] = stats.get("dislikes")
        result["categories"] = [topic.get("name") for topic in topics]
        result["tags"] = [tag.get("text") for tag in tags]
        result["is_live"] = False
        result["thumbnail"] = links.get("thumbnail").get("href")

        manifest_url = links.get("manifest", {}).get("href")
        manifest = self._download_json(manifest_url, url_id)

        manifest_formats = manifest["formats"]
        temp_formats = {}
        for key, value in manifest_formats.items():
            format_result = {
                "vcodec": value.get("videoCodec"),
                "acodec": value.get("audioCodec"),
                "format_note": key,
                "ext": key.split("-")[0],
                "manifest": value.get("manifest"),
            }

            encodings = value.get("encodings")
            if encodings:
                for encoding in encodings:
                    temp_result = deepcopy(format_result)
                    temp_result["url"] = encoding["location"]
                    temp_result["width"] = encoding.get("videoWidth")
                    temp_result["height"] = encoding.get("videoHeight")
                    temp_result["resolution"] = str(encoding.get("videoWidth")) + "x" \
                        + str(encoding.get("videoHeight"))
                    temp_result["vbr"] = encoding.get("videoKbps")
                    temp_result["abr"] = encoding.get("audioKbps")
                    if temp_result["vbr"] and temp_result["abr"]:
                        temp_result["tbr"] = temp_result["vbr"] + temp_result["abr"]
                    else:
                        temp_result["tbr"] = temp_result["vbr"] or temp_result["abr"]
                    if temp_result["tbr"] and result["duration"]:
                        temp_result["filesize_approx"] = temp_result["tbr"] \
                            * result["duration"] * 1024
                    temp_result["format"] = str(encoding.get("videoHeight")) + "p"
                    temp_result["format_id"] = str(temp_result["height"]
                        or temp_result["vbr"]
                        or temp_result["width"])
                    temp_formats[temp_result["format_id"]] = temp_result
            else:
                format_result["url"] = value["origin"]["location"]
                format_result["format"] = "Source"
                format_result["format_id"] = format_result["format"]
                temp_formats["99999"] = format_result
        result["formats"] = [value for key, value in sorted(temp_formats.items())]

        return result

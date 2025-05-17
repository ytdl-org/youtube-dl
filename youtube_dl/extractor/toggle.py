import json
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    parse_iso8601,
    strip_or_none,
)


class ToggleIE(InfoExtractor):
    IE_NAME = "toggle"
    _VALID_URL = r"(?:https?://(?:(?:www\.)?mewatch|video\.toggle)\.sg/(?:[^/]+/){1,}|toggle:)[^/]+-(?P<id>[0-9]+)"
    _TESTS = [
        {
            ### to be updated
            ### deprecated
            # 'url': 'http://www.mewatch.sg/en/series/lion-moms-tif/trailers/lion-moms-premier/343115',
            "info_dict": {
                "id": "343115",
                "ext": "mp4",
                "title": "Lion Moms Premiere",
                "description": "md5:aea1149404bff4d7f7b6da11fafd8e6b",
                "upload_date": "20150910",
                "timestamp": 1441858274,
            },
            "params": {
                "skip_download": "m3u8 download",
            },
        },
        {
            "note": "DRM-protected video",
            ### url deprecated
            # 'url': 'http://www.mewatch.sg/en/movies/dug-s-special-mission/341413',
            "info_dict": {
                "id": "341413",
                "ext": "wvm",
                "title": "Dug's Special Mission",
                "description": "md5:e86c6f4458214905c1772398fabc93e0",
                "upload_date": "20150827",
                "timestamp": 1440644006,
            },
            "params": {
                "skip_download": "DRM-protected wvm download",
            },
        },
        {
            # this also tests correct video id extraction
            "note": "m3u8 links are geo-restricted, but Android/mp4 is okay",
            ### url deprecated
            # 'url': 'http://www.mewatch.sg/en/series/28th-sea-games-5-show/28th-sea-games-5-show-ep11/332861',
            "info_dict": {
                "id": "332861",
                "ext": "mp4",
                "title": "28th SEA Games (5 Show) -  Episode  11",
                "description": "md5:3cd4f5f56c7c3b1340c50a863f896faa",
                "upload_date": "20150605",
                "timestamp": 1433480166,
            },
            "params": {
                "skip_download": "DRM-protected wvm download",
            },
            "skip": "m3u8 links are geo-restricted",
        },
        {
            ### video.toggle.sg seems deprecated
            # 'url': 'http://video.toggle.sg/en/clips/seraph-sun-aloysius-will-suddenly-sing-some-old-songs-in-high-pitch-on-set/343331',
            "only_matching": True,
        },
        {
            "url": "https://www.mewatch.sg/clips/Seraph-Sun-Aloysius-will-suddenly-sing-some-old-songs-in-high-pitch-on-set-84901",
            "only_matching": True,
        },
        {
            "url": "https://www.mewatch.sg/episode/Zero-Calling-S2-E13-The-End-of-The-Beginning-55137",
            "only_matching": True,
        },
        {
            ### webisodes no longer used
            "url": "https://www.mewatch.sg/clips/Jeeva-is-an-orphan-Vetri-S2-Webisode-7-84944",
            # 'url': 'http://www.mewatch.sg/en/series/vetri-s2/webisodes/jeeva-is-an-orphan-vetri-s2-webisode-7/342302',
            "only_matching": True,
        },
        {
            ### only available in Singapore 403 forbidden
            "url": "https://www.mewatch.sg/movie/Seven-Days-79641",
            "only_matching": True,
        },
        {
            ### not working for this list, but not a big issue since old path deprecated
            "url": "https://www.mewatch.sg/list/CNA-Singapore-Tonight-154904",
            # 'url': 'https://www.mewatch.sg/en/tv-show/news/may-2017-cna-singapore-tonight/fri-19-may-2017/512456',
            "only_matching": True,
        },
        {
            ### not working. seems deprecated
            # 'url': 'http://www.mewatch.sg/en/channels/eleven-plus/401585',
            "only_matching": True,
        },
        {
            ### [20230507:shouldsee] working
            "url": "https://www.mewatch.sg/watch/Seraph-Sun-Aloysius-will-suddenly-sing-some-old-songs-in-high-pitch-on-set-84901",
            "only_matching": True,
        },
    ]

    _API_USER = "tvpapi_147"
    _API_PASS = "11111"

    def _real_extract(self, url):
        video_id = self._match_id(url)

        lang = "en"
        params = {
            "delivery": "stream,progressive",
            "resolution": "External",
            "segments": "all",
            "lang": lang,
            "ff": "idp,ldp,rpt,cd",
        }
        video_info = self._download_json(
            "https://cdn.mewatch.sg/api/items/" + video_id + "/videos",
            video_id,
            "Downloading video info json",
            query=params,
        )

        params = {
            # 'delivery':'stream,progressive',
            # 'resolution':'External',
            "segments": "all",
            "lang": lang,
            "ff": "idp,ldp,rpt,cd",
        }
        meta_info = self._download_json(
            "https://cdn.mewatch.sg/api/items/" + video_id,
            video_id,
            "Downloading video info json",
            query=params,
        )

        # urls = info
        info = {"Files": video_info}
        info.update(meta_info)

        title = info["path"].rsplit("/", 1)[-1]
        formats = []

        for video_file in info.get("Files", []):
            video_url, vid_format = video_file.get("url"), video_file.get("format")
            if not video_url or video_url == "NA" or not vid_format:
                continue
            ext = determine_ext(video_url)
            vid_format = vid_format.replace(" ", "")
            # if geo-restricted, m3u8 is inaccessible, but mp4 is okay
            if ext == "m3u8":
                m3u8_formats = self._extract_m3u8_formats(
                    video_url,
                    video_id,
                    ext="mp4",
                    m3u8_id=vid_format,
                    note="Downloading %s m3u8 information" % vid_format,
                    errnote="Failed to download %s m3u8 information" % vid_format,
                    fatal=False,
                )
                for f in m3u8_formats:
                    # Apple FairPlay Streaming
                    if "/fpshls/" in f["url"]:
                        continue
                    formats.append(f)
            elif ext == "mpd":
                formats.extend(
                    self._extract_mpd_formats(
                        video_url,
                        video_id,
                        mpd_id=vid_format,
                        note="Downloading %s MPD manifest" % vid_format,
                        errnote="Failed to download %s MPD manifest" % vid_format,
                        fatal=False,
                    )
                )
            elif ext == "ism":
                formats.extend(
                    self._extract_ism_formats(
                        video_url,
                        video_id,
                        ism_id=vid_format,
                        note="Downloading %s ISM manifest" % vid_format,
                        errnote="Failed to download %s ISM manifest" % vid_format,
                        fatal=False,
                    )
                )
            elif ext == "mp4":
                formats.append(
                    {
                        "ext": ext,
                        "url": video_url,
                        "format_id": vid_format,
                    }
                )
        if not formats:
            for meta in info.get("Metas") or []:
                if (
                    not self.get_param("allow_unplayable_formats")
                    and meta.get("Key") == "Encryption"
                    and meta.get("Value") == "1"
                ):
                    self.report_drm(video_id)
            # Most likely because geo-blocked if no formats and no DRM

        thumbnails = []
        for picture in info.get("images", []):
            if not isinstance(picture, dict):
                continue
            pic_url = picture.get("tile")
            if not pic_url:
                continue
            thumbnail = {
                "url": pic_url,
            }
            pic_size = picture.get("PicSize", "")
            m = re.search(r"(?P<width>\d+)[xX](?P<height>\d+)", pic_size)
            if m:
                thumbnail.update(
                    {
                        "width": int(m.group("width")),
                        "height": int(m.group("height")),
                    }
                )
            thumbnails.append(thumbnail)

        def counter(prefix):
            return int_or_none(
                info.get(prefix + "Counter") or info.get(prefix.lower() + "_counter")
            )

        return {
            "id": video_id,
            "title": title,
            "description": strip_or_none(info.get("Description")),
            "duration": int_or_none(info.get("Duration")),
            "timestamp": parse_iso8601(info.get("CreationDate") or None),
            "average_rating": float_or_none(info.get("Rating")),
            "view_count": counter("View"),
            "like_count": counter("Like"),
            "thumbnails": thumbnails,
            "formats": formats,
        }


class MeWatchIE(InfoExtractor):
    IE_NAME = "mewatch"
    _VALID_URL = (
        r"https?://(?:(?:www|live)\.)?mewatch\.sg/watch/[^/?#&]+-(?P<id>[0-9]+)"
    )
    _TESTS = [
        {
            "url": "https://www.mewatch.sg/watch/Recipe-Of-Life-E1-179371",
            "info_dict": {
                "id": "1008625",
                "ext": "mp4",
                "title": "Recipe Of Life 味之道",
                "timestamp": 1603306526,
                "description": "md5:6e88cde8af2068444fc8e1bc3ebf257c",
                "upload_date": "20201021",
            },
            "params": {
                "skip_download": "m3u8 download",
            },
        },
        {
            "url": "https://www.mewatch.sg/watch/Little-Red-Dot-Detectives-S2-搜密。打卡。小红点-S2-E1-176232",
            "only_matching": True,
        },
        {
            "url": "https://www.mewatch.sg/watch/Little-Red-Dot-Detectives-S2-%E6%90%9C%E5%AF%86%E3%80%82%E6%89%93%E5%8D%A1%E3%80%82%E5%B0%8F%E7%BA%A2%E7%82%B9-S2-E1-176232",
            "only_matching": True,
        },
        {
            "url": "https://live.mewatch.sg/watch/Recipe-Of-Life-E41-189759",
            "only_matching": True,
        },
    ]

    def _real_extract(self, url):
        item_id = self._match_id(url)
        return self.url_result("toggle:" + item_id, ToggleIE.ie_key(), item_id)

        print(f"[debug]{item_id}")
        xdata = self._download_json(
            "https://cdn.mewatch.sg/api/items/" + item_id,
            item_id,
            query={"segments": "all", "lang": "en", "ff": "idp,ldp,rpt,cd"},
        )
        from pprint import pprint

        pprint(xdata)
        custom_id = xdata["customId"]
        print(f"[debug]{custom_id}")
        return self.url_result("toggle:" + custom_id, ToggleIE.ie_key(), custom_id)

# coding: utf-8
from __future__ import unicode_literals

import time
import json
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
    str_or_none,
    str_to_int,
    sanitized_Request,
    urlencode_postdata,
    ExtractorError,
)


class BasicAcfunInfoExtractor(InfoExtractor):
    _FAKE_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # noqa
        "Accept-Charset": "UTF-8,*;q=0.5",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0",  # noqa
    }

    def _extract_formats(self, currentVideoInfo):
        durationMillis = currentVideoInfo.get("durationMillis")
        if "ksPlayJson" in currentVideoInfo:
            ksPlayJson = ksPlayJson = json.loads(currentVideoInfo["ksPlayJson"])
            representation = ksPlayJson.get("adaptationSet")[0].get("representation")

        formats = []
        for stream in representation:
            avgByterate = float_or_none(stream.get("avgBitrate"), 8)
            size = float_or_none(durationMillis, invscale=avgByterate)
            formats += [
                {
                    "url": stream["url"],
                    "ext": "mp4",
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "filesize": size,
                }
            ]
        formats = formats[::-1]
        self._sort_formats(formats)
        return formats


class AcfunIE(BasicAcfunInfoExtractor):
    _VALID_URL = r"https?://www\.acfun\.cn/v/ac(?P<id>\d+)(?P<page_id>[_\d]+)?"
    _TESTS = [
        {
            "note": "single video without playlist",
            "url": "https://www.acfun.cn/v/ac18184362",
            "info_dict": {
                "id": "18184362",
                "ext": "mp4",
                "duration": 192.042,
                "title": "【AC娘】魔性新单《极乐857》上线！来和AC娘一起云蹦迪吧！",
                "uploader": "AC娘本体",
                "uploader_id": 23682490,
            },
        },
        {
            "note": "single video in playlist",
            "url": "https://www.acfun.cn/v/ac17532274_3",
            "info_dict": {
                "id": "17532274_3",
                "ext": "mp4",
                "duration": 233.770,
                "title": "【AC娘x竾颜音】【周六狂欢24小时】TRAP：七夕恋歌！落入本娘爱的陷阱！-TRAP 阿婵",
                "uploader": "AC娘本体",
                "uploader_id": 23682490,
            },
        },
        {
            "note": "multiple video within playlist",
            "url": "https://www.acfun.cn/v/ac17532274",
            "info_dict": {
                "id": "17532274",
                "title": "【AC娘x竾颜音】【周六狂欢24小时】TRAP：七夕恋歌！落入本娘爱的陷阱！",
                "uploader": "AC娘本体",
                "uploader_id": 23682490,
            },
            "playlist_count": 5,
        },
    ]

    def _real_extract(self, url):
        video_id, page_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, video_id, headers=self._FAKE_HEADERS)

        json_text = self._html_search_regex(
            r"(?s)videoInfo\s*=\s*(\{.*?\});", webpage, "json_text"
        )
        json_data = json.loads(json_text)

        title = json_data["title"]

        uploader = str_or_none(json_data.get("user").get("name"))
        uploader_id = str_to_int(json_data.get("user").get("id"))

        videoList = json_data.get("videoList")
        if videoList:
            video_num = len(videoList)

        if not page_id and video_num and video_num > 1:
            if not self._downloader.params.get("noplaylist"):
                self.to_screen(
                    "Downloading all pages of %s(ac%s) - add --no-playlist to just download video"
                    % (title, video_id)
                )
                entries = [
                    self.url_result(
                        "%s_%d" % (url, pid),
                        self.IE_NAME,
                        video_id="%s_%d" % (video_id, pid),
                    )
                    for pid in range(1, video_num + 1)
                ]
                playlist = self.playlist_result(entries, video_id, title)
                playlist.update(
                    {
                        "uploader": uploader,
                        "uploader_id": uploader_id,
                    }
                )
                return playlist

            self.to_screen(
                "Downloading just video %s(ac%s) because of --no-playlist"
                % (title, video_id)
            )

        p_title = self._html_search_regex(
            r"<li\s[^<]*?class='[^']*active[^']*'.*?>(.*?)</li>",
            webpage,
            "p_title",
            default=None,
        )

        if p_title:
            title = "%s-%s" % (title, p_title)

        if page_id:
            video_id += page_id

        currentVideoInfo = json_data.get("currentVideoInfo")
        durationMillis = currentVideoInfo.get("durationMillis")
        duration = float_or_none(durationMillis, 1000)

        formats = self._extract_formats(currentVideoInfo)
        return {
            "id": video_id,
            "uploader_id": uploader_id,
            "title": title,
            "uploader": uploader,
            "duration": duration,
            "formats": formats,
        }


class AcfunBangumiIE(BasicAcfunInfoExtractor):
    _VALID_URL = r"https?://www\.acfun\.cn/bangumi/aa(?P<id>\d+)(?P<episode_id>[_\d]+)?"
    _TESTS = [
        {
            "note": "single episode",
            "url": "https://www.acfun.cn/bangumi/aa6002917_36188_1748679",
            "info_dict": {
                "id": "6002917_36188_1748679",
                "ext": "mp4",
                "duration": 1437.076,
                "title": "租借女友 第12话 告白和女友",
            },
        },
        {
            "note": "all episodes of bangumi",
            "url": "https://www.acfun.cn/bangumi/aa6002917",
            "info_dict": {
                "id": "6002917",
                "title": "租借女友",
            },
            "playlist_count": 12,
        },
    ]

    _TEMPLATE_URL = "https://www.acfun.cn/bangumi/aa%s%s"
    _FETCH_EPISODES_URL = "https://www.acfun.cn/bangumi/aa%s?pagelets=pagelet_partlist&reqID=0&ajaxpipe=1&t=%d"

    def _all_episodes(self, bangumi_id):
        timestamp = int_or_none(float_or_none(time.time(), invscale=1000))
        webpage = self._download_webpage(
            self._FETCH_EPISODES_URL % (bangumi_id, timestamp),
            bangumi_id,
            headers=self._FAKE_HEADERS,
        )
        entries = [
            self.url_result(self._TEMPLATE_URL % (bangumi_id, eid), self.IE_NAME, eid)
            for eid in re.findall(
                r"data-href=./bangumi/aa%s([_\d]+)." % bangumi_id, webpage
            )
        ]
        return entries

    def _real_extract(self, url):
        bangumi_id, episode_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, bangumi_id, headers=self._FAKE_HEADERS)

        json_text = self._html_search_regex(
            r"(?s)bangumiData\s*=\s*(\{.*?\});", webpage, "json_text"
        )
        json_data = json.loads(json_text)

        bangumiTitle = json_data["bangumiTitle"]

        if not episode_id:
            if not self._downloader.params.get("noplaylist"):
                self.to_screen(
                    "Downloading all episodes of %s(aa%s) - add --no-playlist to just download first episode"
                    % (bangumiTitle, bangumi_id)
                )
                playlist = self.playlist_result(
                    self._all_episodes(bangumi_id), bangumi_id, bangumiTitle
                )
                return playlist

            self.to_screen(
                "Downloading just first episode %s(aa%s) because of --no-playlist"
                % (bangumiTitle, bangumi_id)
            )

        title = json_data.get("showTitle") or "%s %s %s" % (
            json_data["bangumiTitle"],
            json_data["episodeName"],
            json_data["title"],
        )

        currentVideoInfo = json_data.get("currentVideoInfo")
        durationMillis = currentVideoInfo.get("durationMillis")
        duration = float_or_none(durationMillis, 1000)

        if episode_id:
            bangumi_id += episode_id

        formats = self._extract_formats(currentVideoInfo)
        return {
            "id": bangumi_id,
            "title": title,
            "duration": duration,
            "formats": formats,
        }


class AcfunLiveIE(BasicAcfunInfoExtractor):
    _VALID_URL = r"https?://live\.acfun\.cn/live/(?P<id>\d+)"
    _TEST = {
        "url": "https://live.acfun.cn/live/34195163",
        "info_dict": {
            "id": "34195163",
            "ext": "mp4",
            "title": r"re:^晴心Haruko \d{4}-\d{2}-\d{2} \d{2}:\d{2}$",
            "is_live": True,
        },
        "only_matching": True,
    }

    _LOGIN_URL = "https://id.app.acfun.cn/rest/app/visitor/login"
    _STREAMS_URL = "https://api.kuaishouzt.com/rest/zt/live/web/startPlay?subBiz=mainApp&kpn=ACFUN_APP&kpf=PC_WEB&userId=%d&did=%s&acfun.api.visitor_st=%s"

    def _real_extract(self, url):
        live_id = self._match_id(url)
        self._FAKE_HEADERS.update({"Referer": url})

        # Firstly fetch _did cookie and streamer name(use for title)
        first_req = sanitized_Request(url, headers=self._FAKE_HEADERS)
        webpage, first_res = self._download_webpage_handle(first_req, live_id)
        live_up_name = self._html_search_regex(
            r"<a [^>]*?class[^>]*?up-name[^>]*?>([^<]*?)</a>",
            webpage,
            "live_up_name",
        )

        for header_name, header_value in first_res.info().items():
            if header_name.lower() == "set-cookie":
                cookies = header_value
        if not cookies:
            raise ExtractorError("Fail to fetch cookies")

        cookies_dict = dict(c.strip(" ,").split("=", 1) for c in cookies.split(";"))
        did_cookie = cookies_dict["_did"]

        self._FAKE_HEADERS.update({"Cookie": "_did=%s" % did_cookie})

        # Login to get userId and acfun.api.visitor_st
        login_data = urlencode_postdata({"sid": "acfun.api.visitor"})
        login_json = self._download_json(
            self._LOGIN_URL,
            live_id,
            data=login_data,
            headers=self._FAKE_HEADERS,
        )

        streams_url = self._STREAMS_URL % (
            login_json["userId"],
            did_cookie,
            login_json["acfun.api.visitor_st"],
        )

        # Fetch stream lists
        fetch_streams_data = urlencode_postdata(
            {"authorId": int_or_none(live_id), "pullStreamType": "FLV"}
        )

        streams_json = self._download_json(
            streams_url, live_id, data=fetch_streams_data, headers=self._FAKE_HEADERS
        )

        try:
            assert "data" in streams_json
        except AssertionError:
            raise ExtractorError("This live room is currently closed")

        streams_info = json.loads(streams_json["data"]["videoPlayRes"])
        representation = streams_info["liveAdaptiveManifest"][0]["adaptationSet"][
            "representation"
        ]

        formats = []
        for stream in representation:
            # use hls instead of flv to fix video broken problem when stopped
            i = stream["url"].index("flv?")
            u3m8_url = (
                stream["url"][0:i].replace("pull.etoote.com", "hlspull.etoote.com")
                + "m3u8"
            )
            formats += [
                {
                    "url": u3m8_url,
                    "ext": "mp4",
                    "tbr": stream.get("bitrate"),
                }
            ]
        self._sort_formats(formats)
        return {
            "id": live_id,
            "title": self._live_title(live_up_name),
            "formats": formats,
            "is_live": True,
        }

# coding: utf-8
from __future__ import unicode_literals
import re
from .common import InfoExtractor, ExtractorError
from ..compat import compat_str


class LineLiveIE(InfoExtractor):
    _VALID_URL = r'https?://live\.line\.me/channels/(?P<CHANNEL_ID>\d+)/broadcast/(?P<id>\d+)/?'

    _TESTS = [
        {
            "url": "https://live.line.me/channels/4867368/broadcast/16331360",
            "md5": "bc931f26bf1d4f971e3b0982b3fab4a3",
            "info_dict": {
                "id": "16331360",
                "title": "振りコピ講座😙😙😙",
                "ext": "mp4",
                "timestamp": 1617095132,
                "upload_date": "20210330"
            }
        },
        {
            "url": "https://live.line.me/channels/5893542/broadcast/16354857",
            "info_dict": {
                "id": "16354857",
                "title": "マイクラ！？がんばるー！！！",
                "ext": "mp4",
                "timestamp": 1617351854,
                "upload_date": "20210402"
            }
        }
    ]

    def _real_extract(self, url):
        channel_id, id = re.match(self._VALID_URL, url).groups()
        data = self._download_json("https://live-api.line-apps.com/web/v4.0/channel/" + channel_id + "/broadcast/" + id, id)
        live_data = data.get("item", None)
        channel_data = live_data.get("channel", None)
        archive_urls = data.get("archivedHLSURLs", None)
        if archive_urls is None:
            raise ExtractorError("archivedHLSURLs not found", expected=True)
        formats = []
        for key, value in archive_urls.items():
            if value is None:
                continue
            formats += self._extract_m3u8_formats(value, id, ext="mp4", entry_protocol="m3u8_native", m3u8_id="hls")
        if len(formats) == 0:
            raise ExtractorError("no archive found", expected=True)
        self._sort_formats(formats)
        return {
            "id": id,
            "title": live_data.get("title", None),
            "formats": formats,
            "timestamp": live_data.get("createdAt", None),
            "duration": live_data.get("archiveDuration", None),
            "channel": channel_data.get("name", None),
            "channel_id": channel_data.get("id", None),
        }


class LineLiveUserIE(InfoExtractor):
    _VALID_URL = r'https?://live\.line\.me/channels/(?P<ID>\d+)/?$'

    _TESTS = [
        {
            "url": "https://live.line.me/channels/5893542",
            "info_dict": {
                "id": "5893542",
                "title": "いくらちゃん",
                "description": str,
            },
            "playlist_count": 29
        }
    ]

    def _real_extract(self, url):
        id = re.match(self._VALID_URL, url).group("ID")
        data = self._download_json("https://live-api.line-apps.com/web/v4.0/channel/" + id, id)
        archived_urls = []
        items = data["archivedBroadcasts"]
        while True:
            for item in items["rows"]:
                archived_urls.append(self.url_result(item["shareURL"], "LineLive"))
            if not items["hasNextPage"]:
                break
            items = self._download_json("https://live-api.line-apps.com/web/v4.0/channel/" + id + "/archived_broadcasts?lastId=" + compat_str(items["rows"][-1]["id"]), id)
        entryes = self.playlist_result(archived_urls, id, data.get("title", None), playlist_description=data.get("information", None))
        return entryes

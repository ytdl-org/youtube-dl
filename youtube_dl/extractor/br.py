# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class BRIE(InfoExtractor):
    IE_DESC = "Bayerischer Rundfunk Mediathek"
    _VALID_URL = r"^https?://(?:www\.)?br\.de/mediathek/video/(?:sendungen/)?(?:[a-z0-9\-/]+/)?(?P<id>[a-z0-9\-]+)\.html$"
    _BASE_URL = "http://www.br.de"

    _TESTS = [
        {
            "url": "http://www.br.de/mediathek/video/anselm-gruen-114.html",
            "md5": "c4f83cf0f023ba5875aba0bf46860df2",
            "info_dict": {
                "id": "2c8d81c5-6fb7-4a74-88d4-e768e5856532",
                "ext": "mp4",
                "title": "Feiern und Verzichten",
                "description": "Anselm Grün: Feiern und Verzichten",
                "uploader": "BR/Birgit Baier",
                "upload_date": "20140301"
            }
        },
        {
            "url": "http://www.br.de/mediathek/video/sendungen/unter-unserem-himmel/unter-unserem-himmel-alpen-ueber-den-pass-100.html",
            "md5": "ab451b09d861dbed7d7cc9ab0be19ebe",
            "info_dict": {
                "id": "2c060e69-3a27-4e13-b0f0-668fac17d812",
                "ext": "mp4",
                "title": "Über den Pass",
                "description": "Die Eroberung der Alpen: Über den Pass",
                "uploader": None,
                "upload_date": None
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        page = self._download_webpage(url, display_id)
        xml_url = self._search_regex(
            r"return BRavFramework\.register\(BRavFramework\('avPlayer_(?:[a-f0-9-]{36})'\)\.setup\({dataURL:'(/mediathek/video/[a-z0-9/~_.-]+)'}\)\);", page, "XMLURL")
        xml = self._download_xml(self._BASE_URL + xml_url, None)

        videos = []
        for xml_video in xml.findall("video"):
            video = {
                "id": xml_video.get("externalId"),
                "title": xml_video.find("title").text,
                "formats": self._extract_formats(xml_video.find("assets")),
                "thumbnails": self._extract_thumbnails(xml_video.find("teaserImage/variants")),
                "description": " ".join(xml_video.find("shareTitle").text.splitlines()),
                "webpage_url": xml_video.find("permalink").text
            }
            if xml_video.find("author").text:
                video["uploader"] = xml_video.find("author").text
            if xml_video.find("broadcastDate").text:
                video["upload_date"] =  "".join(reversed(xml_video.find("broadcastDate").text.split(".")))
            videos.append(video)

        if len(videos) > 1:
            self._downloader.report_warning(
                'found multiple videos; please '
                'report this with the video URL to http://yt-dl.org/bug')
        if not videos:
            raise ExtractorError('No video entries found')
        return videos[0]

    def _extract_formats(self, assets):
        formats = [{
            "url": asset.find("downloadUrl").text,
            "ext": asset.find("mediaType").text,
            "format_id": asset.get("type"),
            "width": int(asset.find("frameWidth").text),
            "height": int(asset.find("frameHeight").text),
            "tbr": int(asset.find("bitrateVideo").text),
            "abr": int(asset.find("bitrateAudio").text),
            "vcodec": asset.find("codecVideo").text,
            "container": asset.find("mediaType").text,
            "filesize": int(asset.find("size").text),
        } for asset in assets.findall("asset")
            if asset.find("downloadUrl") is not None]

        self._sort_formats(formats)
        return formats

    def _extract_thumbnails(self, variants):
        thumbnails = [{
            "url": self._BASE_URL + variant.find("url").text,
            "width": int(variant.find("width").text),
            "height": int(variant.find("height").text),
        } for variant in variants.findall("variant")]
        thumbnails.sort(key=lambda x: x["width"] * x["height"], reverse=True)
        return thumbnails

# coding: utf-8
from __future__ import unicode_literals

from urllib import parse

from .common import InfoExtractor

from ..utils import clean_html, unified_timestamp


class ParlerIE(InfoExtractor):
    """Extract videos from posts on Parler."""

    _VALID_URL = r"https://parler\.com/feed/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    _TESTS = [
        {
            "url": "https://parler.com/feed/df79fdba-07cc-48fe-b085-3293897520d7",
            "md5": "16e0f447bf186bb3cf64de5bbbf4d22d",
            "info_dict": {
                "id": "df79fdba-07cc-48fe-b085-3293897520d7",
                "ext": "mp4",
                "title": "Puberty-blocking procedures promoted by the Biden/Harris Admin are child abuse. The FDA has recently confirmed these hormones/drugs have extremely dangerous side effects, like brain swelling and vision loss.",
                "timestamp": 1659744000,
                "upload_date": "20220806",
                "uploader": "Tulsi Gabbard",
                "uploader_id": "TulsiGabbard",
            },
        },
        {
            "url": "https://parler.com/feed/a7406eb4-91e5-4793-b5e3-ade57a24e287",
            "md5": "11687e2f5bb353682cee338d181422ed",
            "info_dict": {
                "id": "a7406eb4-91e5-4793-b5e3-ade57a24e287",
                "ext": "mp4",
                "title": "This man should run for office",
                "timestamp": 1659657600,
                "upload_date": "20220805",
                "uploader": "Benny Johnson",
                "uploader_id": "BennyJohnson",
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Get data from API
        api_url = "https://parler.com/open-api/ParleyDetailEndpoint.php"
        payload = parse.urlencode({"uuid": video_id}).encode()
        status = self._download_json(api_url, video_id, data=payload)

        # Pull out video
        data = status["data"][0]["primary"]
        video = data["video_data"]
        url = video["videoSrc"]

        # Pull out metadata
        title = clean_html(data.get("full_body")).replace("\n", "")
        timestamp = unified_timestamp(data.get("date_created"))
        uploader = data.get("name")
        uploader_id = data.get("username")
        uploader_url = "https://parler.com/" + uploader_id if uploader_id else None

        # Return the result
        return {
            "id": video_id,
            "url": url,
            "title": title,
            "timestamp": timestamp,
            "uploader": uploader,
            "uploader_id": uploader_id,
            "uploader_url": uploader_url,
        }

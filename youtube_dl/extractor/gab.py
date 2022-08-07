# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import clean_html, int_or_none, unified_timestamp


class GabIE(InfoExtractor):
    """Extract videos from posts on Gab."""

    _VALID_URL = r"https://gab\.com/@[^/]+/posts/(?P<id>[0-9]+)"
    _TESTS = [
        {
            "url": "https://gab.com/INFOWARS/posts/108732338582726706",
            "md5": "4a5fb1470c192e493d9efd6f19e514d3",
            "info_dict": {
                "id": "108732338582726706",
                "ext": "mp4",
                "title": "Untitled",
                "timestamp": 1659835827,
                "upload_date": "20220729",
                "uploader": "INFOWARS",
                "uploader_id": "INFOWARS",
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        print(video_id)

        # Get data from API
        api_url = "https://gab.com/api/v1/statuses/" + video_id
        status = self._download_json(api_url, video_id)
        print(status)

        # Pull out video
        attachments = status["media_attachments"]
        video = attachments[0]
        url = video["source_mp4"]
        print(url)

        # Pull out metadata
        title = clean_html(status.get("content")).replace("\n", "") or "Untitled"
        account = status.get("account") or {}
        timestamp = unified_timestamp(status.get("created_at"))
        uploader = account.get("display_name")
        uploader_id = account.get("username")
        uploader_url = (
            "https://gab.com/@" + uploader_id if uploader_id else None
        )
        repost_count = int_or_none(status.get("reblogs_count"))
        like_count = int_or_none(status.get("favourites_count"))
        comment_count = int_or_none(status.get("replies_count"))

        return {
            "id": video_id,
            "url": url,
            "title": title,
            "timestamp": timestamp,
            "uploader": uploader,
            "uploader_id": uploader_id,
            "uploader_url": uploader_url,
            "repost_count": repost_count,
            "like_count": like_count,
            "comment_count": comment_count,
        }

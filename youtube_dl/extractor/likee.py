# coding: utf-8
# Code by hatienl0i261299 - fb.com/100011734236090 - hatienloi261299@gmail.com
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode
)
from ..utils import (
    js_to_json,
    int_or_none,
    try_get
)


class LikeeIE(InfoExtractor):
    _VALID_URL = r'''(?x)^((http[s]?|fpt):)\/?\/(www\.|m\.|)
            (?P<site>
                (likee\.com)
            )\/(?P<user>@.+?)\/(video)\/(?P<id>[0-9]+)$
            '''
    IE_NAME = 'likee'
    IE_DESC = 'likee.com'
    _TESTS = [
        {
            "url": "https://likee.com/@Inayat95/video/6808497581927578387",
            "info_dict": {
                "id": "6808497581927578387",
                "ext": "mp4",
                "title": "@Inayat95_6808497581927578387",
                "description": str,
                "thumbnail": r"re:^https?:.+?.jpg",
                "uploader": str,
                "uploader_id": int,
                "like_count": int,
                "comment_count": int,
                "share_count": int,
                "view_count": int,
                "download_count": int
            }
        },
        {
            "url": "https://likee.com/@Inayat95/video/6792552721999608595",
            "info_dict": {
                "id": "6792552721999608595",
                "ext": "mp4",
                "title": "@Inayat95_6792552721999608595",
                "description": str,
                "thumbnail": r"re:^https?:.+?.jpg",
                "uploader": str,
                "uploader_id": int,
                "like_count": int,
                "comment_count": int,
                "share_count": int,
                "view_count": int,
                "download_count": int
            }
        },
        {
            "url": "https://likee.com/@435421183/video/6802046076516688592",
            "info_dict": {
                "id": "6802046076516688592",
                "ext": "mp4",
                "title": "@435421183_6802046076516688592",
                "description": str,
                "thumbnail": r"re:^https?:.+?.jpg",
                "uploader": str,
                "uploader_id": int,
                "like_count": int,
                "comment_count": int,
                "share_count": int,
                "view_count": int,
                "download_count": int
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group("id")
        user = mobj.group("user")
        webpage = self._download_webpage(
            url_or_request=url,
            video_id=video_id
        )

        info_video = self._regex_data(webpage, video_id)

        if info_video.get("post_id") == video_id:
            formats = [{
                "url": info_video.get("video_url") or info_video.get("video_water_url"),
                "ext": "mp4",
                "height": int_or_none(info_video.get("video_height")),
                "width": int_or_none(info_video.get("video_width")),
                "protocol": "http",
            }]

            def get_count(name):
                return int_or_none(info_video.get(name), default=0)

            return {
                "id": video_id,
                "title": "%s_%s" % (user, video_id),
                "description": info_video.get("msg_text") or '',
                "thumbnail": info_video.get("image1") or info_video.get("image2") or info_video.get("image3"),
                "like_count": get_count("like_count"),
                "view_count": get_count("play_count"),
                "share_count": get_count("share_count"),
                "download_count": get_count("download_count"),
                "comment_count": get_count("comment_count"),
                "uploader": info_video.get("nick_name"),
                "uploader_id": int_or_none(info_video.get("poster_uid")),
                "formats": formats
            }

    def _regex_data(self, webpage, video_id):
        info_video = self._parse_json(self._search_regex(
            r'''<script>window.data\s+=\s+(\{.+?\})\;''',
            webpage,
            "info video",
        ), video_id, transform_source=js_to_json)
        return info_video


class LikeeUserIE(LikeeIE):
    _VALID_URL = r'''(?x)^((http[s]?|fpt):)\/?\/(www\.|m\.|)
            (?P<site>
                (likee\.com)
            )\/(user)\/(?P<user>@.*?)(\W|$)
            '''
    IE_NAME = "likee:user"
    _TESTS = [
        {
            "url": "https://likee.com/user/@Inayat95",
            "info_dict": {
                "id": "1357265683",
                "title": "@Inayat95",
            },
            "playlist_mincount": 10
        },
        {
            "url": "https://likee.com/user/@435421183/",
            "info_dict": {
                "id": "681435856",
                "title": "@435421183",
            },
            "playlist_mincount": 5
        },
        {
            "url": "https://likee.com/user/@52710468/",
            "info_dict": {
                "id": "1300330468",
                "title": "@52710468",
            },
            "playlist_mincount": 10
        }
    ]

    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)

        user = mobj.group("user")

        webpage = self._download_webpage(
            url_or_request=url,
            video_id=user
        )
        info_playlist = self._regex_data(webpage, user)
        uid = try_get(info_playlist, lambda x: x['userinfo']['uid'])

        return self.playlist_result(entries=self._entries(uid, user), playlist_id=uid, playlist_title=user)

    def _entries(self, uid, user):
        count = 50
        lastPostId = ""
        while True:
            info = self._download_json(
                url_or_request="https://likee.com/official_website/VideoApi/getUserVideo",
                video_id=lastPostId or uid,
                data=compat_urllib_parse_urlencode({
                    "uid": uid,
                    "count": count,
                    "lastPostId": lastPostId
                }).encode()
            )
            if info.get("msg") != "success":
                break
            videoList = try_get(info, lambda x: x['data']['videoList'])
            video_id = ''
            for video in videoList:
                if not video:
                    continue
                video_id = video.get("postId")
                yield self.url_result(
                    url="https://likee.com/%s/video/%s" % (user, video_id),
                    ie=LikeeIE.ie_key(),
                    video_id=video_id
                )
            lastPostId = video_id
            if len(videoList) != count:
                break

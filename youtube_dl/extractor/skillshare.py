from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    try_get,
    unified_timestamp
)


class SkillshareBaseIE(InfoExtractor):
    _NETRC_MACHINE = "skillshare"

    _TN_RE = r"uploads/video/thumbnails/[0-9a-f]+/(?P<width>[0-9]+)-(?P<height>[0-9]+)"
    _LOGIN_URL = "https://api.skillshare.com/login"
    _VIDEO_URL = "https://api.skillshare.com/sessions/%s/download"

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None or password is None:
            self.raise_login_required("An email and password is needed to download any video (even non-premium ones)")

        data = {
            "email": username,
            "password": password
        }
        headers = {
            "Content-Type": "application/json"
        }
        user_json = self._download_json(self._LOGIN_URL,
                                        None,
                                        note="Logging in",
                                        errnote="Error logging in, make sure the email and password is correct",
                                        data=json.dumps(data).encode(),
                                        headers=headers)

        user_type = user_json.get("membership_label", "Premium Member")
        if user_type == "Basic Member":
            self._user_type = 0
        elif user_type == "Premium Member":
            self._user_type = 2
        else:
            raise ExtractorError("User type %s unknown" % user_json["membership_label"])


# I can find no way of linking to a specific video so only entire course downloads are available.
class SkillshareCourseIE(SkillshareBaseIE):
    IE_NAME = 'skillshare:course'
    IE_DESC = 'skillshare.com classes'
    _VALID_URL = r'https?://(?:www\.)?skillshare\.com/classes/[^/]+/(?P<id>[0-9]+)'

    _CLASS_URL = "https://api.skillshare.com/classes/%s"

    _TEST = {
        "url": "https://www.skillshare.com/classes/Blender-3D-Fire-Smoke-Simulation-Guide/1850126092",
        "only_matching": True
    }

    def _real_extract(self, url):
        # Technically the SKU, not ID but the SKU is a more universal identifier.
        class_id = self._match_id(url)
        class_json = self._download_json(self._CLASS_URL % class_id,
                                         None,
                                         note="Getting class details",
                                         errnote="Downloading class JSON")

        if class_json.get("enrollment_type", 0) > self._user_type:
            raise ExtractorError("This course requires a premium account and thus can't be downloaded")

        lessons_json = []
        # Pretty sure all classes only have one unit but flattening just in case.
        for unit_json in class_json["_embedded"]["units"]["_embedded"]["units"]:
            lessons_json += (unit_json["_embedded"]["sessions"]["_embedded"]["sessions"])

        videos = []
        for lesson_json in lessons_json:
            lesson_thumbnail_urls = [
                lesson_json.get("video_thumbnail_url"),
                lesson_json.get("video_thumbnail_url"),
                lesson_json.get("image_thumbnail")
            ]
            lesson_thumbnail_urls = filter(None, lesson_thumbnail_urls)
            lesson_thumbnails_json = []
            for lesson_thumbnail_url in lesson_thumbnail_urls:
                lesson_thumbnails_json.append({
                    "url": lesson_thumbnail_url,
                    "width": int_or_none(self._search_regex(self._TN_RE, lesson_thumbnail_url, "width", fatal=False)),
                    "height": int_or_none(self._search_regex(self._TN_RE, lesson_thumbnail_url, "height", fatal=False)),
                })
            if not lesson_thumbnails_json:
                lesson_thumbnails_json = None

            lesson_categories = [class_json.get("category")]
            if lesson_categories == [None]:
                lesson_categories = None

            videos.append({
                "id": compat_str(lesson_json["id"]),
                "title": lesson_json.get("title"),
                "url": self._VIDEO_URL % compat_str(lesson_json["id"]),
                "ext": "mp4",
                "thumbnails": lesson_thumbnails_json,
                "uploader": try_get(class_json, lambda x: x["_embedded"]["teacher"]["full_name"]),
                "creator": try_get(class_json, lambda x: x["_embedded"]["teacher"]["full_name"]),
                "timestamp": unified_timestamp(lesson_json.get("create_time")),
                "uploader_id": compat_str(try_get(class_json, lambda x: x["_embedded"]["teacher"]["username"])),
                "categories": lesson_categories,
                "chapter": try_get(lesson_json, lambda x: x["_links"]["unit"]["title"]),
                "chapter_id": compat_str(lesson_json.get("unit_id"))
            })

        return {
            "id": class_id,
            "title": class_json["title"],
            "uploader": try_get(class_json, lambda x: x["_embedded"]["teacher"]["full_name"]),
            "uploader_id": compat_str(try_get(class_json, lambda x: x["_embedded"]["teacher"]["username"])),
            "_type": "playlist",
            "entries": videos
        }

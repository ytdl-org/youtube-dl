from .common import InfoExtractor
from .. import utils


class YouMakerIE(InfoExtractor):
    _VALID_URL = r"""(?x)
                    https?://(?:www\.)?youmaker\.com/
                    (?:v|video|embed)/
                    (?P<id>[0-9a-zA-Z-]+)
                    """

    _TESTS = [
        {
            "url": "https://www.youmaker.com/v/Dnnrq0lw8062",
            "info_dict": {
                "id": "77c92592-57fa-4bfc-a5da-79e965667001",
                "ext": "mp4",
                "title": "Althistoriker Dr. David Engels im Interview: „Das ist der echte Untergang des Abendlandes“",
                "description": "Im Interview mit Epoch Times führt der belgische Althistoriker Dr. David Engels aus, "
                "wie sich der Zerfall der europäischen Staatengemeinschaft im Zuge der Corona-Krise zugespitzt hat, "
                "und zeichnet Parallelen zu den letzten Atemzügen der spätrömischen Republik. \n\n"
                "Der Artikel zu dem Interview folgt in Kürze hier: https://www.epochtimes.de/wissen/"
                "gesellschaft/das-ist-der-echte-untergang-des-abendlandes-a3613553.html",
                "duration": 3507,
                "upload_date": "20211001",
                "uploader": "Deepochtimes",
                "timestamp": 1633079621,
                "channel": "Epoch Times Deutsch",
                "channel_id": "9a7c740c-74c7-4ebb-86ad-611ba4e71535",
            },
            "params": {
                "skip_download": True,
                "nocheckcertificate": True,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            "https://youmaker.com/v1/api/video/metadata/%s" % video_id, video_id
        )

        status = info.get("status", "something went wrong")
        if status != "ok":
            raise utils.ExtractorError(status, expected=True)

        info = info["data"]
        video_info = info.get("data", "")
        duration = video_info.get("duration")
        formats = []
        playlist = video_info.get("videoAssets", {}).get("Stream")

        if playlist:
            formats.extend(
                self._extract_m3u8_formats(
                    playlist,
                    video_id,
                    ext="mp4",
                )
            )

        if formats:
            self._sort_formats(formats)
            for item in formats:
                item["format_id"] = "hls-%dp" % item["height"]
                if duration and item.get("tbr"):
                    item["filesize_approx"] = 128 * item["tbr"] * duration

        return {
            "id": info["video_uid"],
            "formats": formats,
            "title": info["title"],
            "description": info["description"],
            "timestamp": utils.parse_iso8601(info["uploaded_at"]),
            "upload_date": utils.unified_strdate(info["uploaded_at"]),
            "uploader": info.get("uploaded_by"),
            "duration": duration,
            "channel": info.get("channel_name"),
            "channel_id": info.get("channel_uid"),
            "channel_url": "https://www.youmaker.com/channel/%s"
            % info.get("channel_uid", ""),
            "thumbnails": [{"url": info["thumbmail_path"]}],
            "view_count": utils.int_or_none(info.get("click")),
        }

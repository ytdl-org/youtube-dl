# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import urlhandle_detect_ext


class TikTokIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tiktok\.com/v/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://m.tiktok.com/v/6606727368545406213.html',
        'md5': '163ceff303bb52de60e6887fe399e6cd',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'Zureeal|TikTok|Global Video Community',
            'thumbnail': 'http://m-p16.akamaized.net/img/tos-maliva-p-0068/5e7a4ec40fb146888fa27aa8d78f86fd~noop.image',
            'description': 'Zureeal has just created an awesome short video with ♬ original sound - joogieboy1596',
            'uploader': 'Zureeal',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_string = self._search_regex(r'var data = ({.*});', webpage, 'json_string')
        json_data = self._parse_json(json_string, video_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        video_url = json_data.get("video").get("play_addr").get("url_list")[0]
        uploader = json_data.get("author").get("nickname")
        thumbnail_list = json_data.get("video").get("cover").get("url_list")
        thumbnail = thumbnail_list[0] if len(thumbnail_list) > 0 else None
        handle = self._download_webpage_handle(video_url, video_id, fatal=False)
        URLHandle = handle[1] if handle is not False else None
        ext = urlhandle_detect_ext(URLHandle)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': video_url,
            'ext': ext,
            'thumbnail': thumbnail,
        }

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urlhandle_detect_ext,
    try_get,
    compat_str,
    url_or_none,
    str_or_none,
)


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

        data = self._parse_json(
            self._search_regex(
                r'var data = ({.*});', webpage, 'json_string', webpage, 'data'
            ), video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        video_url = url_or_none(
            try_get(data, lambda x: x['video']['play_addr']['url_list'][0], compat_str))

        uploader = try_get(data, lambda x: x['author']['nickname'], compat_str)

        thumbnail = url_or_none(
            try_get(
                data, lambda x: x['video']['cover']['url_list'][0], compat_str))

        ext = str_or_none(
            urlhandle_detect_ext(
                self._request_webpage(video_url, video_id, fatal=False)))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': video_url,
            'ext': ext,
            'thumbnail': thumbnail,
        }

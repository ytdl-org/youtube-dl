# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    remove_end,
)


class LRTIE(InfoExtractor):
    IE_NAME = 'lrt.lt'
    _VALID_URL = r'https?://(?:www\.)?lrt\.lt/mediateka/irasas/(?P<id>[0-9]+)'
    _TESTS = [{
        # m3u8 download
        'url': 'https://www.lrt.lt/mediateka/irasas/54391/septynios-kauno-dienos',
        'md5': '50c84b875e930784daa66fa8c2617664',
        'info_dict': {
            'id': '54391',
            'ext': 'mp4',
            'title': 'Septynios Kauno dienos',
            'description': 'md5:24d84534c7dc76581e59f5689462411a',
        },
    }, {
        # after the redesign - everything is mp4 file (some of the shows used to be mp3)
        'url': 'https://www.lrt.lt/mediateka/irasas/1013074524/kita-tema-2016-09-05-15-05',
        'md5': 'e286cd475ad2839ab90c2ec0be57930b',
        'info_dict': {
            'id': '1013074524',
            'ext': 'mp4',
            'title': 'Kita tema 2016-09-05 15:05',
            'description': 'md5:1b295a8fc7219ed0d543fc228c931fb5',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = remove_end(self._og_search_title(webpage), ' - LRT')

        file_url1 = ""
        urlinfo = ""

        formats = []
        for _, file_url in re.findall(
                r'(main_url) = "(.*)";', webpage):
            urlinfo = self._download_json("https://www.lrt.lt/servisai/stream_url/vod/media_info/?url=" + file_url, video_id)

            file_url1 = urlinfo.get("playlist_item").get("file")

            release_date_string_temp = urlinfo.get("date")
            release_date = release_date_string_temp[0:4] + release_date_string_temp[5:7] + release_date_string_temp[8:10]

            ext = determine_ext(file_url1)
            if ext not in ('m3u8', 'mp3'):
                continue
            # mp3 served as m3u8 produces stuttered media file
            if ext == 'm3u8' and '.mp3' in file_url1:
                continue
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    file_url1, video_id, 'mp4', entry_protocol='m3u8_native',
                    fatal=False))
            elif ext == 'mp3':
                formats.append({
                    'url': file_url1,
                    'vcodec': 'none',
                })
        self._sort_formats(formats)

        try:
            thumbnail = self._og_search_thumbnail(webpage)
        except:
            thumbnail = 0

        description = urlinfo.get("content")

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'release_date': release_date
        }

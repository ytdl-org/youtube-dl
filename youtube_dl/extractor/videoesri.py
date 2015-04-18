# coding: utf-8
from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor

from ..utils import (
    unified_strdate
)


class VideoEsriIE(InfoExtractor):
    _VALID_URL = r'https?://video\.esri\.com/watch/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://video.esri.com/watch/4228',
        'md5': '170b4d513c2466ed483c150a48384133',
        'info_dict': {
            'id': '4228',
            'ext': 'mp4',
            'title': 'AppStudio for ArcGIS',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20150310',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title')

        upload_date_raw = self._search_regex(
            r'http-equiv="last-modified" content="(.*)"',
            webpage, 'upload date')
        upload_date = unified_strdate(upload_date_raw)

        settings_info = self._search_regex(
            r'evPlayerSettings = {(.*?);\s*$',
            webpage, 'settings info', flags=re.MULTILINE | re.DOTALL)

        # thumbnail includes '_x' for large, also has {_m,_t,_s} or
        # without size suffix returns full image
        thumbnail_path = re.findall(
            r'image\': \'(\/thumbs.*)\'',
            settings_info)[0]

        if thumbnail_path:
            thumbnail = '/'.join(['http://video.esri.com', thumbnail_path])

        # note that this misses the (exceedly rare) webm files
        video_paths = re.findall(r'mp4:(.*)\'', settings_info)

        # find possible http servers of the mp4 files (also has rtsp)
        base_url = re.findall(
            r'netstreambasepath\':\s\'(h.*)\'', settings_info)[0]

        # these are the numbers used internally, but really map
        # to other resolutions, e.g. 960 is 720p.
        heights = [480, 720, 960]
        videos_by_res = {}
        for video_path in video_paths:
            url = "{base_url}{video_path}".format(
                base_url=base_url,
                video_path=video_path)
            filename, ext = os.path.splitext(video_path)
            height_label = int(filename.split('_')[1])
            videos_by_res[height_label] = {
                'url': url,
                'ext': ext[1:],
                'protocol': 'http',  # http-only supported currently
            }

        formats = []
        for height in heights:
            if height in videos_by_res:
                formats.append(videos_by_res[height])

        result = {
            'id': video_id,
            'title': title,
            'upload_date': upload_date,
            'formats': formats,
        }

        if thumbnail:
            result['thumbnail'] = thumbnail

        return result

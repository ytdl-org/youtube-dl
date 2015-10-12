# coding: utf-8
from __future__ import unicode_literals

import os
import urlparse

from youtube_dl import utils
from .common import InfoExtractor


class CanvasIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?canvas\.be/video/(?P<id>.+)'
    _TEST = {
        'url': 'http://www.canvas.be/video/de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
        'md5': 'ea838375a547ac787d4064d8c7860a6c',
        'info_dict': {
            'id': 'de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
            'title': 'De afspraak veilt voor de Warmste Week',
            'ext': 'mp4',
            'duration': 49,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(
            r'<h1 class="video__body__header__title">(.+?)</h1>', webpage,
            'title')
        data_video = self._html_search_regex(
            r'data-video=(["\'])(?P<id>.+?)\1', webpage, 'data-video', group='id')
        json_url = 'https://mediazone.vrt.be/api/v1/canvas/assets/' + data_video
        data = self._download_json(json_url, video_id)

        formats = []
        for target in data['targetUrls']:
            if 'type' and 'url' in target:
                extension = utils.determine_ext(target['url'])
                if target['type'] == 'PROGRESSIVE_DOWNLOAD':
                    formats.append({
                        'format_id': extension,
                        'url': target['url'],
                        'protocol': 'http',
                    })
                elif target['type'] == 'HLS':
                    formats.extend(self._extract_m3u8_formats(
                        target['url'], video_id, entry_protocol='m3u8_native',
                        ext='mp4',
                        preference=0,
                        fatal=False,
                        m3u8_id='hls'))
                elif target['type'] == 'HDS':
                    formats.append({
                        'format_id': extension,
                        'url': target['url'],
                        'protocol': 'HDS',
                    })
                elif target['type'] == 'RTMP':
                    formats.append({
                        'format_id': extension,
                        'url': target['url'],
                        'protocol': 'rtmp',
                    })
                elif target['type'] == 'RTSP':
                    formats.append({
                        'format_id': extension,
                        'url': target['url'],
                        'protocol': 'rtsp',
                    })

        self._sort_formats(formats)
        duration = utils.int_or_none(data.get('duration')) / 1000
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration,
        }

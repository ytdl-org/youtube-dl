# coding: utf-8
from __future__ import unicode_literals

import re

from youtube_dl.utils import try_get, str_or_none

from .common import InfoExtractor


class MacProVideoBaseIE(InfoExtractor):
    def _get_video_info(self, data):
        meta = data.get('ned_programmanifest')
        video_id = str_or_none(meta.get('fk_videoMediaID'))

        formats = self._extract_m3u8_formats(
            data['video_medium']['mediaURL'], video_id, 'mp4', m3u8_id='hls', fatal=False)
        self._sort_formats(formats)

        description = try_get(data, lambda x: x['ned_programmanifest_description']['description'])
        thumbnail = try_get(data, lambda x: x['thumbnail_medium']['mediaURL'])

        return {
            'id': video_id,
            'title': meta.get('vid_title'),
            'description': description,
            'thumbnail': thumbnail,
            'duration': meta.get('vid_duration'),
            'formats': formats
        }


class MacProVideoIE(MacProVideoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?macprovideo\.com/video/(?P<course>[0-9a-zA-Z-]+)/(?P<num>[0-9]+)-[0-9a-zA-Z-]+'
    _TEST = {
        'url': 'https://www.macprovideo.com/video/apple-logic-pro-102-recording-and-editing-audio/1-1-transducers-and-converters',
        'md5': 'md5:608d7c8cf9f31202cbd269273df62aaf',
        'info_dict': {
            'id': '319676',
            'ext': 'mp4',
            'title': '1. Transducers and Converters',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:c16dc8a42252e2be44225f129c591c3d',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
            'format': 'bestvideo'
        },
    }

    def _real_extract(self, url):
        course, num = re.match(self._VALID_URL, url).groups()
        num = int(num) - 1
        data = self._download_json('https://www.macprovideo.com/ajax/videos/' + course,
                                   None)['data']['videos'][num]
        return self._get_video_info(data)


class MacProVideoCourseIE(MacProVideoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?macprovideo\.com/course/(?P<id>[0-9a-zA-Z-]+)'
    _TEST = {
        'url': 'https://www.macprovideo.com/course/apple-logic-pro-102-recording-and-editing-audio',
        'md5': 'md5:608d7c8cf9f31202cbd269273df62aaf',
        'info_dict': {
            'id': '319676',
            'ext': 'mp4',
            'title': '1. Transducers and Converters',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:c16dc8a42252e2be44225f129c591c3d',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
            'format': 'bestvideo'
        },
    }

    def _real_extract(self, url):
        course_id = self._match_id(url)
        videos = self._download_json('https://www.macprovideo.com/ajax/videos/' + course_id, None)['data']['videos']
        title = try_get(videos, lambda x: x[0]['tutorial']['tu_title'])

        return self.playlist_result(
            [self._get_video_info(data) for data in videos],
            playlist_id=course_id, playlist_title=title)

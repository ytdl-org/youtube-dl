# coding: utf-8
from .common import InfoExtractor


class ReshetIE(InfoExtractor):
    _VALID_URL = r'http://(mood\.)?reshet\.tv/'
    _TEST = {
        'url': 'http://reshet.tv/item/entertainment/the-voice/branded/skittles/clips/jimmy-47659/',
        'md5': 'b56f1f91915cc931389ad3ea1e90e61f',
        'info_dict': {
            'id': '5235248235001',
            'ext': 'mp4',
            'title': 'The Voice ישראל - הכירו את ג\'ימי החתול | רשת',
            'description': 'יש לנו כתב דיגיטל חדש ופרוע מאחורי הקלעים של The Voice ישראל . תגידו מיאו',
            'thumbnail': 'http://reshet.tv/wp-content/uploads/2016/12/Capture-1.jpg',
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'video id')
        video_id = self._html_search_regex(r'data-video-id=\'(\d+)\'', webpage, 'video id')
        m3u8_url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=' + video_id
        formats = []
        formats.extend(self._extract_m3u8_formats(m3u8_url, video_id, 'mp4'))
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail
        }

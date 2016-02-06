# coding: utf-8
from __future__ import unicode_literals

import hmac
from hashlib import sha1
from base64 import b64encode
from time import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none
)
from ..compat import compat_urllib_parse


class VLiveIE(InfoExtractor):
    IE_NAME = 'vlive'
    # vlive.tv/video/ links redirect to www.vlive.tv/video/ 
    _VALID_URL = r'https?://(?:(www|m)\.)?vlive\.tv/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.vlive.tv/video/1326',
        'md5': 'cc7314812855ce56de70a06a27314983',
        'info_dict': {
            'id': '1326',
            'ext': 'mp4',
            'title': '[V] Girl\'s Day\'s Broadcast',
            'creator': 'Girl\'s Day',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.vlive.tv/video/%s' % video_id,
            video_id, note='Download video page')

        long_video_id = self._search_regex(
            r'vlive\.tv\.video\.ajax\.request\.handler\.init\("[0-9]+",\s?"[^"]*",\s?"([^"]+)",\s?"[^"]+",\s?"[^"]*",\s?"[^"]*"\)', webpage, 'long_video_id')

        key = self._search_regex(
            r'vlive\.tv\.video\.ajax\.request\.handler\.init\("[0-9]+",\s?"[^"]*",\s?"[^"]+",\s?"([^"]+)",\s?"[^"]*",\s?"[^"]*"\)', webpage, 'key')

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        creator = self._html_search_regex(
            r'<div class="info_area">\s*<strong[^>]+class="name">([^<>]+)</strong>', webpage, 'creator',fatal=False)

        # doct = document type (xml or json), cpt = caption type (vtt or ttml)
        url = "http://global.apis.naver.com/rmcnmv/rmcnmv/vod_play_videoInfo.json?videoId=%s&key=%s&ptc=http&doct=json&cpt=vtt" % (long_video_id, key)
        
        playinfo = self._download_json(url, video_id, 'Downloading video json')

        formats = []
        for vid in playinfo.get('videos', {}).get('list', []):
            formats.append({
                'url': vid['source'],
                'ext': 'mp4',
                'abr': vid.get('bitrate', {}).get('audio'),
                'vbr': vid.get('bitrate', {}).get('video'),
                'format_id': vid.get('encodingOption', {}).get('name'),
                'height': int_or_none(vid.get('encodingOption', {}).get('height')),
                'width': int_or_none(vid.get('encodingOption', {}).get('width')),
            })
        self._sort_formats(formats)

        subtitles = {}
        for caption in playinfo.get('captions', {}).get('list', []):
            subtitles[caption['language']] = [
                {'ext': determine_ext(caption['source'], default_ext='vtt'),
                 'url': caption['source']}]

        return {
            'id': video_id,
            'title': title,
            'creator': creator,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }

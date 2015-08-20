# coding: utf-8
from __future__ import unicode_literals

import hmac
from hashlib import sha1
from base64 import b64encode
from time import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext
)
from ..compat import compat_urllib_parse


class VLiveIE(InfoExtractor):
    IE_NAME = 'vlive'
    _VALID_URL = r'https?://(?:(www|m)\.)?vlive\.tv/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://m.vlive.tv/video/1326',
        'md5': 'cc7314812855ce56de70a06a27314983',
        'info_dict': {
            'id': '1326',
            'ext': 'mp4',
            'title': '[V] Girl\'s Day\'s Broadcast',
            'creator': 'Girl\'s Day',
            'upload_date': '20150817',
        },
    }
    _SECRET = 'rFkwZet6pqk1vQt6SxxUkAHX7YL3lmqzUMrU4IDusTo4jEBdtOhNfT4BYYAdArwH'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://m.vlive.tv/video/%s' % video_id,
            video_id, note='Download video page')

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        creator = self._html_search_regex(
            r'<span class="name">([^<>]+)</span>', webpage, 'creator')
        upload_date = self._html_search_regex(
            r'<span class="time">(\d{4}\.\d{2}\.\d{2})</span>', webpage,
            'upload date', default=None, fatal=False)
        if upload_date:
            upload_date = upload_date.replace('.', '')

        url = 'http://global.apis.naver.com/globalV/globalV/vod/%s/playinfo?' % video_id
        msgpad = {'msgpad': '%.0f' % (time() * 1000)}
        md = {
            'md': b64encode(
                hmac.new(self._SECRET.encode('ascii'),
                         (url[:255] + msgpad['msgpad']).encode('ascii'), sha1).digest())
        }
        url += '&' + compat_urllib_parse.urlencode(msgpad) + '&' + compat_urllib_parse.urlencode(md)

        playinfo = self._download_json(url, video_id, 'Downloading video json')

        if playinfo.get('message', '') != 'success':
            raise ExtractorError(playinfo['message'])

        if not playinfo.get('result'):
            raise ExtractorError('No videos found.')

        formats = []
        for vid in playinfo['result'].get('videos', {}).get('list', []):
            formats.append({
                'url': vid['source'],
                'ext': 'mp4',
                'abr': vid.get('bitrate', {}).get('audio'),
                'vbr': vid.get('bitrate', {}).get('video'),
                'format_id': vid['encodingOption']['name'],
                'height': vid.get('height'),
                'width': vid.get('width'),
            })
        self._sort_formats(formats)

        subtitles = {}
        for caption in playinfo['result'].get('captions', {}).get('list', []):
            subtitles[caption['language']] = [
                {'ext': determine_ext(caption['source'], default_ext='vtt'),
                 'url': caption['source']}]

        return {
            'id': video_id,
            'title': title,
            'creator': creator,
            'thumbnail': thumbnail,
            'formats': formats,
            'upload_date': upload_date,
            'subtitles': subtitles,
        }

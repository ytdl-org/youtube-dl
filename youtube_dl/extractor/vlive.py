# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    dict_get,
    float_or_none,
    int_or_none,
)
from ..compat import compat_urllib_parse_urlencode


class VLiveIE(InfoExtractor):
    IE_NAME = 'vlive'
    _VALID_URL = r'https?://(?:(?:www|m)\.)?vlive\.tv/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.vlive.tv/video/1326',
        'md5': 'cc7314812855ce56de70a06a27314983',
        'info_dict': {
            'id': '1326',
            'ext': 'mp4',
            'title': "[V] Girl's Day's Broadcast",
            'creator': "Girl's Day",
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.vlive.tv/video/%s' % video_id, video_id)

        long_video_id = self._search_regex(
            r'vlive\.tv\.video\.ajax\.request\.handler\.init\(\s*"[0-9]+"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"',
            webpage, 'long video id')

        key = self._search_regex(
            r'vlive\.tv\.video\.ajax\.request\.handler\.init\(\s*"[0-9]+"\s*,\s*"[^"]*"\s*,\s*"[^"]+"\s*,\s*"([^"]+)"',
            webpage, 'key')

        title = self._og_search_title(webpage)

        playinfo = self._download_json(
            'http://global.apis.naver.com/rmcnmv/rmcnmv/vod_play_videoInfo.json?%s'
            % compat_urllib_parse_urlencode({
                'videoId': long_video_id,
                'key': key,
                'ptc': 'http',
                'doct': 'json',  # document type (xml or json)
                'cpt': 'vtt',  # captions type (vtt or ttml)
            }), video_id)

        formats = [{
            'url': vid['source'],
            'format_id': vid.get('encodingOption', {}).get('name'),
            'abr': float_or_none(vid.get('bitrate', {}).get('audio')),
            'vbr': float_or_none(vid.get('bitrate', {}).get('video')),
            'width': int_or_none(vid.get('encodingOption', {}).get('width')),
            'height': int_or_none(vid.get('encodingOption', {}).get('height')),
            'filesize': int_or_none(vid.get('size')),
        } for vid in playinfo.get('videos', {}).get('list', []) if vid.get('source')]
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        creator = self._html_search_regex(
            r'<div[^>]+class="info_area"[^>]*>\s*<a\s+[^>]*>([^<]+)',
            webpage, 'creator', fatal=False)

        view_count = int_or_none(playinfo.get('meta', {}).get('count'))

        subtitles = {}
        for caption in playinfo.get('captions', {}).get('list', []):
            lang = dict_get(caption, ('language', 'locale', 'country', 'label'))
            if lang and caption.get('source'):
                subtitles[lang] = [{
                    'ext': 'vtt',
                    'url': caption['source']}]

        return {
            'id': video_id,
            'title': title,
            'creator': creator,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
            'subtitles': subtitles,
        }

# coding: utf-8
from __future__ import division, unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    dict_get,
    ExtractorError,
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

        # UTC+x - UTC+9 (KST)
        tz = time.altzone if time.localtime().tm_isdst == 1 else time.timezone
        tz_offset = -tz // 60 - 9 * 60
        self._set_cookie('vlive.tv', 'timezoneOffset', '%d' % tz_offset)

        status_params = self._download_json(
            'http://www.vlive.tv/video/status?videoSeq=%s' % video_id,
            video_id, 'Downloading JSON status',
            headers={'Referer': url.encode('utf-8')})
        status = status_params.get('status')
        air_start = status_params.get('onAirStartAt', '')
        is_live = status_params.get('isLive')

        video_params = self._search_regex(
            r'vlive\.tv\.video\.ajax\.request\.handler\.init\((.+)\)',
            webpage, 'video params')
        live_params, long_video_id, key = re.split(
            r'"\s*,\s*"', video_params)[1:4]

        if status == 'LIVE_ON_AIR' or status == 'BIG_EVENT_ON_AIR':
            live_params = self._parse_json('"%s"' % live_params, video_id)
            live_params = self._parse_json(live_params, video_id)
            return self._live(video_id, webpage, live_params)
        elif status == 'VOD_ON_AIR' or status == 'BIG_EVENT_INTRO':
            if long_video_id and key:
                return self._replay(video_id, webpage, long_video_id, key)
            elif is_live:
                status = 'LIVE_END'
            else:
                status = 'COMING_SOON'

        if status == 'LIVE_END':
            raise ExtractorError('Uploading for replay. Please wait...',
                                 expected=True)
        elif status == 'COMING_SOON':
            raise ExtractorError('Coming soon! %s' % air_start, expected=True)
        elif status == 'CANCELED':
            raise ExtractorError('We are sorry, '
                                 'but the live broadcast has been canceled.',
                                 expected=True)
        else:
            raise ExtractorError('Unknown status %s' % status)

    def _get_common_fields(self, webpage):
        title = self._og_search_title(webpage)
        creator = self._html_search_regex(
            r'<div[^>]+class="info_area"[^>]*>\s*<a\s+[^>]*>([^<]+)',
            webpage, 'creator', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        return {
            'title': title,
            'creator': creator,
            'thumbnail': thumbnail,
        }

    def _live(self, video_id, webpage, live_params):
        formats = []
        for vid in live_params.get('resolutions', []):
            formats.extend(self._extract_m3u8_formats(
                vid['cdnUrl'], video_id, 'mp4',
                m3u8_id=vid.get('name'),
                fatal=False, live=True))
        self._sort_formats(formats)

        return dict(self._get_common_fields(webpage),
                    id=video_id,
                    formats=formats,
                    is_live=True)

    def _replay(self, video_id, webpage, long_video_id, key):
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

        view_count = int_or_none(playinfo.get('meta', {}).get('count'))

        subtitles = {}
        for caption in playinfo.get('captions', {}).get('list', []):
            lang = dict_get(caption, ('language', 'locale', 'country', 'label'))
            if lang and caption.get('source'):
                subtitles[lang] = [{
                    'ext': 'vtt',
                    'url': caption['source']}]

        return dict(self._get_common_fields(webpage),
                    id=video_id,
                    formats=formats,
                    view_count=view_count,
                    subtitles=subtitles)

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    int_or_none,
    remove_start,
    urlencode_postdata,
)
from ..compat import compat_urllib_parse_urlencode


class VLiveIE(InfoExtractor):
    IE_NAME = 'vlive'
    _VALID_URL = r'https?://(?:(?:www|m)\.)?vlive\.tv/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.vlive.tv/video/1326',
        'md5': 'cc7314812855ce56de70a06a27314983',
        'info_dict': {
            'id': '1326',
            'ext': 'mp4',
            'title': "[V LIVE] Girl's Day's Broadcast",
            'creator': "Girl's Day",
            'view_count': int,
        },
    }, {
        'url': 'http://www.vlive.tv/video/16937',
        'info_dict': {
            'id': '16937',
            'ext': 'mp4',
            'title': '[V LIVE] 첸백시 걍방',
            'creator': 'EXO',
            'view_count': int,
            'subtitles': 'mincount:12',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.vlive.tv/video/%s' % video_id, video_id)

        VIDEO_PARAMS_RE = r'\bvlive\.video\.init\(([^)]+)'
        VIDEO_PARAMS_FIELD = 'video params'

        params = self._parse_json(self._search_regex(
            VIDEO_PARAMS_RE, webpage, VIDEO_PARAMS_FIELD, default=''), video_id,
            transform_source=lambda s: '[' + s + ']', fatal=False)

        if not params or len(params) < 7:
            params = self._search_regex(
                VIDEO_PARAMS_RE, webpage, VIDEO_PARAMS_FIELD)
            params = [p.strip(r'"') for p in re.split(r'\s*,\s*', params)]

        status, long_video_id, key = params[2], params[5], params[6]
        status = remove_start(status, 'PRODUCT_')

        if status == 'LIVE_ON_AIR' or status == 'BIG_EVENT_ON_AIR':
            return self._live(video_id, webpage)
        elif status == 'VOD_ON_AIR' or status == 'BIG_EVENT_INTRO':
            if long_video_id and key:
                return self._replay(video_id, webpage, long_video_id, key)
            else:
                status = 'COMING_SOON'

        if status == 'LIVE_END':
            raise ExtractorError('Uploading for replay. Please wait...',
                                 expected=True)
        elif status == 'COMING_SOON':
            raise ExtractorError('Coming soon!', expected=True)
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

    def _live(self, video_id, webpage):
        init_page = self._download_webpage(
            'http://www.vlive.tv/video/init/view',
            video_id, note='Downloading live webpage',
            data=urlencode_postdata({'videoSeq': video_id}),
            headers={
                'Referer': 'http://www.vlive.tv/video/%s' % video_id,
                'Content-Type': 'application/x-www-form-urlencoded'
            })

        live_params = self._search_regex(
            r'"liveStreamInfo"\s*:\s*(".*"),',
            init_page, 'live stream info')
        live_params = self._parse_json(live_params, video_id)
        live_params = self._parse_json(live_params, video_id)

        formats = []
        for vid in live_params.get('resolutions', []):
            formats.extend(self._extract_m3u8_formats(
                vid['cdnUrl'], video_id, 'mp4',
                m3u8_id=vid.get('name'),
                fatal=False, live=True))
        self._sort_formats(formats)

        info = self._get_common_fields(webpage)
        info.update({
            'title': self._live_title(info['title']),
            'id': video_id,
            'formats': formats,
            'is_live': True,
        })
        return info

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
            lang = dict_get(caption, ('locale', 'language', 'country', 'label'))
            if lang and caption.get('source'):
                subtitles[lang] = [{
                    'ext': 'vtt',
                    'url': caption['source']}]

        info = self._get_common_fields(webpage)
        info.update({
            'id': video_id,
            'formats': formats,
            'view_count': view_count,
            'subtitles': subtitles,
        })
        return info

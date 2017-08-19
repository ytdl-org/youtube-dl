# coding: utf-8
from __future__ import unicode_literals

import re
import time
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_str,
)
from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    int_or_none,
    remove_start,
    try_get,
    urlencode_postdata,
)


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

    @classmethod
    def suitable(cls, url):
        return False if VLivePlaylistIE.suitable(url) else super(VLiveIE, cls).suitable(url)

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

        if status in ('LIVE_ON_AIR', 'BIG_EVENT_ON_AIR'):
            return self._live(video_id, webpage)
        elif status in ('VOD_ON_AIR', 'BIG_EVENT_INTRO'):
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


class VLiveChannelIE(InfoExtractor):
    IE_NAME = 'vlive:channel'
    _VALID_URL = r'https?://channels\.vlive\.tv/(?P<id>[0-9A-Z]+)'
    _TEST = {
        'url': 'http://channels.vlive.tv/FCD4B',
        'info_dict': {
            'id': 'FCD4B',
            'title': 'MAMAMOO',
        },
        'playlist_mincount': 110
    }
    _APP_ID = '8c6cc7b45d2568fb668be6e05b6e5a3b'

    def _real_extract(self, url):
        channel_code = self._match_id(url)

        webpage = self._download_webpage(
            'http://channels.vlive.tv/%s/video' % channel_code, channel_code)

        app_id = None

        app_js_url = self._search_regex(
            r'<script[^>]+src=(["\'])(?P<url>http.+?/app\.js.*?)\1',
            webpage, 'app js', default=None, group='url')

        if app_js_url:
            app_js = self._download_webpage(
                app_js_url, channel_code, 'Downloading app JS', fatal=False)
            if app_js:
                app_id = self._search_regex(
                    r'Global\.VFAN_APP_ID\s*=\s*[\'"]([^\'"]+)[\'"]',
                    app_js, 'app id', default=None)

        app_id = app_id or self._APP_ID

        channel_info = self._download_json(
            'http://api.vfan.vlive.tv/vproxy/channelplus/decodeChannelCode',
            channel_code, note='Downloading decode channel code',
            query={
                'app_id': app_id,
                'channelCode': channel_code,
                '_': int(time.time())
            })

        channel_seq = channel_info['result']['channelSeq']
        channel_name = None
        entries = []

        for page_num in itertools.count(1):
            video_list = self._download_json(
                'http://api.vfan.vlive.tv/vproxy/channelplus/getChannelVideoList',
                channel_code, note='Downloading channel list page #%d' % page_num,
                query={
                    'app_id': app_id,
                    'channelSeq': channel_seq,
                    # Large values of maxNumOfRows (~300 or above) may cause
                    # empty responses (see [1]), e.g. this happens for [2] that
                    # has more than 300 videos.
                    # 1. https://github.com/rg3/youtube-dl/issues/13830
                    # 2. http://channels.vlive.tv/EDBF.
                    'maxNumOfRows': 100,
                    '_': int(time.time()),
                    'pageNo': page_num
                }
            )

            if not channel_name:
                channel_name = try_get(
                    video_list,
                    lambda x: x['result']['channelInfo']['channelName'],
                    compat_str)

            videos = try_get(
                video_list, lambda x: x['result']['videoList'], list)
            if not videos:
                break

            for video in videos:
                video_id = video.get('videoSeq')
                if not video_id:
                    continue
                video_id = compat_str(video_id)
                entries.append(
                    self.url_result(
                        'http://www.vlive.tv/video/%s' % video_id,
                        ie=VLiveIE.ie_key(), video_id=video_id))

        return self.playlist_result(
            entries, channel_code, channel_name)


class VLivePlaylistIE(InfoExtractor):
    IE_NAME = 'vlive:playlist'
    _VALID_URL = r'https?://(?:(?:www|m)\.)?vlive\.tv/video/(?P<video_id>[0-9]+)/playlist/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.vlive.tv/video/22867/playlist/22912',
        'info_dict': {
            'id': '22912',
            'title': 'Valentine Day Message from TWICE'
        },
        'playlist_mincount': 9
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, playlist_id = mobj.group('video_id', 'id')

        VIDEO_URL_TEMPLATE = 'http://www.vlive.tv/video/%s'
        if self._downloader.params.get('noplaylist'):
            self.to_screen(
                'Downloading just video %s because of --no-playlist' % video_id)
            return self.url_result(
                VIDEO_URL_TEMPLATE % video_id,
                ie=VLiveIE.ie_key(), video_id=video_id)

        self.to_screen(
            'Downloading playlist %s - add --no-playlist to just download video'
            % playlist_id)

        webpage = self._download_webpage(
            'http://www.vlive.tv/video/%s/playlist/%s'
            % (video_id, playlist_id), playlist_id)

        item_ids = self._parse_json(
            self._search_regex(
                r'playlistVideoSeqs\s*=\s*(\[[^]]+\])', webpage,
                'playlist video seqs'),
            playlist_id)

        entries = [
            self.url_result(
                VIDEO_URL_TEMPLATE % item_id, ie=VLiveIE.ie_key(),
                video_id=compat_str(item_id))
            for item_id in item_ids]

        playlist_name = self._html_search_regex(
            r'<div[^>]+class="[^"]*multicam_playlist[^>]*>\s*<h3[^>]+>([^<]+)',
            webpage, 'playlist title', fatal=False)

        return self.playlist_result(entries, playlist_id, playlist_name)

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
)


class LimelightBaseIE(InfoExtractor):
    _PLAYLIST_SERVICE_URL = 'http://production-ps.lvp.llnw.net/r/PlaylistService/%s/%s/%s'
    _API_URL = 'http://api.video.limelight.com/rest/organizations/%s/%s/%s/%s.json'

    def _call_playlist_service(self, item_id, method, fatal=True):
        return self._download_json(
            self._PLAYLIST_SERVICE_URL % (self._PLAYLIST_SERVICE_PATH, item_id, method),
            item_id, 'Downloading PlaylistService %s JSON' % method, fatal=fatal)

    def _call_api(self, organization_id, item_id, method):
        return self._download_json(
            self._API_URL % (organization_id, self._API_PATH, item_id, method),
            item_id, 'Downloading API %s JSON' % method)

    def _extract(self, item_id, pc_method, mobile_method, meta_method):
        pc = self._call_playlist_service(item_id, pc_method)
        metadata = self._call_api(pc['orgId'], item_id, meta_method)
        mobile = self._call_playlist_service(item_id, mobile_method, fatal=False)
        return pc, mobile, metadata

    def _extract_info(self, streams, mobile_urls, properties):
        video_id = properties['media_id']
        formats = []

        for stream in streams:
            stream_url = stream.get('url')
            if not stream_url:
                continue
            if '.f4m' in stream_url:
                formats.extend(self._extract_f4m_formats(stream_url, video_id))
            else:
                fmt = {
                    'url': stream_url,
                    'abr': float_or_none(stream.get('audioBitRate')),
                    'vbr': float_or_none(stream.get('videoBitRate')),
                    'fps': float_or_none(stream.get('videoFrameRate')),
                    'width': int_or_none(stream.get('videoWidthInPixels')),
                    'height': int_or_none(stream.get('videoHeightInPixels')),
                    'ext': determine_ext(stream_url)
                }
                rtmp = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>.+))/(?P<playpath>mp4:.+)$', stream_url)
                if rtmp:
                    format_id = 'rtmp'
                    if stream.get('videoBitRate'):
                        format_id += '-%d' % int_or_none(stream['videoBitRate'])
                    fmt.update({
                        'url': rtmp.group('url'),
                        'play_path': rtmp.group('playpath'),
                        'app': rtmp.group('app'),
                        'ext': 'flv',
                        'format_id': format_id,
                    })
                formats.append(fmt)

        for mobile_url in mobile_urls:
            media_url = mobile_url.get('mobileUrl')
            if not media_url:
                continue
            format_id = mobile_url.get('targetMediaPlatform')
            if determine_ext(media_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=-1, m3u8_id=format_id))
            else:
                formats.append({
                    'url': media_url,
                    'format_id': format_id,
                    'preference': -1,
                })

        self._sort_formats(formats)

        title = properties['title']
        description = properties.get('description')
        timestamp = int_or_none(properties.get('publish_date') or properties.get('create_date'))
        duration = float_or_none(properties.get('duration_in_milliseconds'), 1000)
        filesize = int_or_none(properties.get('total_storage_in_bytes'))
        categories = [properties.get('category')]
        tags = properties.get('tags', [])
        thumbnails = [{
            'url': thumbnail['url'],
            'width': int_or_none(thumbnail.get('width')),
            'height': int_or_none(thumbnail.get('height')),
        } for thumbnail in properties.get('thumbnails', []) if thumbnail.get('url')]

        subtitles = {}
        for caption in properties.get('captions', {}):
            lang = caption.get('language_code')
            subtitles_url = caption.get('url')
            if lang and subtitles_url:
                subtitles[lang] = [{
                    'url': subtitles_url,
                }]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'timestamp': timestamp,
            'duration': duration,
            'filesize': filesize,
            'categories': categories,
            'tags': tags,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
        }


class LimelightMediaIE(LimelightBaseIE):
    IE_NAME = 'limelight'
    _VALID_URL = r'(?:limelight:media:|http://link\.videoplatform\.limelight\.com/media/\??\bmediaId=)(?P<id>[a-z0-9]{32})'
    _TESTS = [{
        'url': 'http://link.videoplatform.limelight.com/media/?mediaId=3ffd040b522b4485b6d84effc750cd86',
        'info_dict': {
            'id': '3ffd040b522b4485b6d84effc750cd86',
            'ext': 'flv',
            'title': 'HaP and the HB Prince Trailer',
            'description': 'md5:8005b944181778e313d95c1237ddb640',
            'thumbnail': 're:^https?://.*\.jpeg$',
            'duration': 144.23,
            'timestamp': 1244136834,
            'upload_date': '20090604',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # video with subtitles
        'url': 'limelight:media:a3e00274d4564ec4a9b29b9466432335',
        'info_dict': {
            'id': 'a3e00274d4564ec4a9b29b9466432335',
            'ext': 'flv',
            'title': '3Play Media Overview Video',
            'description': '',
            'thumbnail': 're:^https?://.*\.jpeg$',
            'duration': 78.101,
            'timestamp': 1338929955,
            'upload_date': '20120605',
            'subtitles': 'mincount:9',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }]
    _PLAYLIST_SERVICE_PATH = 'media'
    _API_PATH = 'media'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        pc, mobile, metadata = self._extract(
            video_id, 'getPlaylistByMediaId', 'getMobilePlaylistByMediaId', 'properties')

        return self._extract_info(
            pc['playlistItems'][0].get('streams', []),
            mobile['mediaList'][0].get('mobileUrls', []) if mobile else [],
            metadata)


class LimelightChannelIE(LimelightBaseIE):
    IE_NAME = 'limelight:channel'
    _VALID_URL = r'(?:limelight:channel:|http://link\.videoplatform\.limelight\.com/media/\??\bchannelId=)(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://link.videoplatform.limelight.com/media/?channelId=ab6a524c379342f9b23642917020c082',
        'info_dict': {
            'id': 'ab6a524c379342f9b23642917020c082',
            'title': 'Javascript Sample Code',
        },
        'playlist_mincount': 3,
    }
    _PLAYLIST_SERVICE_PATH = 'channel'
    _API_PATH = 'channels'

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        pc, mobile, medias = self._extract(
            channel_id, 'getPlaylistByChannelId',
            'getMobilePlaylistWithNItemsByChannelId?begin=0&count=-1', 'media')

        entries = [
            self._extract_info(
                pc['playlistItems'][i].get('streams', []),
                mobile['mediaList'][i].get('mobileUrls', []) if mobile else [],
                medias['media_list'][i])
            for i in range(len(medias['media_list']))]

        return self.playlist_result(entries, channel_id, pc['title'])


class LimelightChannelListIE(LimelightBaseIE):
    IE_NAME = 'limelight:channel_list'
    _VALID_URL = r'(?:limelight:channel_list:|http://link\.videoplatform\.limelight\.com/media/\?.*?\bchannelListId=)(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://link.videoplatform.limelight.com/media/?channelListId=301b117890c4465c8179ede21fd92e2b',
        'info_dict': {
            'id': '301b117890c4465c8179ede21fd92e2b',
            'title': 'Website - Hero Player',
        },
        'playlist_mincount': 2,
    }
    _PLAYLIST_SERVICE_PATH = 'channel_list'

    def _real_extract(self, url):
        channel_list_id = self._match_id(url)

        channel_list = self._call_playlist_service(channel_list_id, 'getMobileChannelListById')

        entries = [
            self.url_result('limelight:channel:%s' % channel['id'], 'LimelightChannel')
            for channel in channel_list['channelList']]

        return self.playlist_result(entries, channel_list_id, channel_list['title'])

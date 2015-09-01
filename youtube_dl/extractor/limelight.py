# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    determine_ext,
)


class LimeLightBaseIE(InfoExtractor):

    def get_playlist_service(self, id, method):
        return self._download_json(self.PLAYLIST_SERVICE_URL % (id, method), id)

    def get_api(self, orgId, id, method):
        return self._download_json(self.API_URL % (orgId, id, method), id)

    def process_data(self, mobileUrls, streams, properties):
        video_id = properties['media_id']
        formats = []

        for mobileUrl in mobileUrls:
            if '.m3u8' in mobileUrl['mobileUrl']:
                formats.extend(self._extract_m3u8_formats(mobileUrl['mobileUrl'], video_id))
            else:
                formats.append({'url': mobileUrl['mobileUrl']})

        for stream in streams:
            if '.f4m' in stream['url']:
                formats.extend(self._extract_f4m_formats(stream['url'], video_id))
            else:
                fmt = {
                    'url': stream.get('url'),
                    'abr': stream.get('audioBitRate'),
                    'vbr': stream.get('videoBitRate'),
                    'fps': stream.get('videoFrameRate'),
                    'width': stream.get('videoWidthInPixels'),
                    'height': stream.get('videoHeightInPixels'),
                    'ext': determine_ext(stream.get('url'))
                }
                rtmp = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>.+))/(?P<playpath>mp4:.+)$', stream['url'])
                if rtmp:
                    fmt.update({
                        'url': rtmp.group('url'),
                        'play_path': rtmp.group('playpath'),
                        'app': rtmp.group('app'),
                    })
                formats.append(fmt)

        self._sort_formats(formats)

        title = properties['title']
        description = properties.get('description')
        timestamp = properties.get('create_date')
        duration = int_or_none(properties.get('duration_in_milliseconds'))
        filesize = properties.get('total_storage_in_bytes')
        categories = [properties.get('category')]
        thumbnails = [{
            'url': thumbnail.get('url'),
            'width': int_or_none(thumbnail.get('width')),
            'height': int_or_none(thumbnail.get('height')),
        } for thumbnail in properties.get('thumbnails')]
        subtitles = {caption.get('language_code'): [{'url': caption.get('url')}] for caption in properties.get('captions')}

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'timestamp': timestamp,
            'duration': duration,
            'filesize': filesize,
            'categories': categories,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
        }


class LimeLightMediaIE(LimeLightBaseIE):
    IE_NAME = 'limelight'
    _VALID_URL = r'http://link\.videoplatform\.limelight\.com/media/?.*mediaId=(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://link.videoplatform.limelight.com/media/?mediaId=3ffd040b522b4485b6d84effc750cd86',
        'md5': '3213605088be599705677ef785db6972',
        'info_dict': {
            'id': '3ffd040b522b4485b6d84effc750cd86',
            'ext': 'mp4',
            'title': 'HaP and the HB Prince Trailer',
            'description': 'As Harry Potter begins his 6th year at Hogwarts School of Witchcraft and Wizardry, he discovers an old book marked mysteriously "This book is the property of the Half-Blood Prince" and begins to learn more about Lord Voldemort\'s dark past.',
            'thumbnail': 're:^https?://.*\.jpeg$',
            'duration': 144230,
            'timestamp': 1244136834,
            "upload_date": "20090604",
        }
    }
    PLAYLIST_SERVICE_URL = 'http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/%s'
    API_URL = 'http://api.video.limelight.com/rest/organizations/%s/media/%s/%s.json'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        mobile_json_data = self.get_playlist_service(video_id, 'getMobilePlaylistByMediaId')
        pc_json_data = self.get_playlist_service(video_id, 'getPlaylistByMediaId')
        properties = self.get_api(pc_json_data['orgId'], video_id, 'properties')

        return self.process_data(mobile_json_data['mediaList'][0]['mobileUrls'], pc_json_data['playlistItems'][0]['streams'], properties)


class LimeLightChannelIE(LimeLightBaseIE):
    IE_NAME = 'limelight:channel'
    _VALID_URL = r'http://link\.videoplatform\.limelight\.com/media/?.*channelId=(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://link.videoplatform.limelight.com/media/?channelId=ab6a524c379342f9b23642917020c082',
        'info_dict': {
            'id': 'ab6a524c379342f9b23642917020c082',
            'title': 'Javascript Sample Code',
        },
        'playlist_mincount': 3,
    }
    PLAYLIST_SERVICE_URL = 'http://production-ps.lvp.llnw.net/r/PlaylistService/channel/%s/%s'
    API_URL = 'http://api.video.limelight.com/rest/organizations/%s/channels/%s/%s.json'

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        mobile_json_data = self.get_playlist_service(channel_id, 'getMobilePlaylistWithNItemsByChannelId?begin=0&count=-1')
        pc_json_data = self.get_playlist_service(channel_id, 'getPlaylistByChannelId')
        medias = self.get_api(pc_json_data['orgId'], channel_id, 'media')

        entries = []
        for i in range(len(medias['media_list'])):
            entries.append(self.process_data(mobile_json_data['mediaList'][i]['mobileUrls'], pc_json_data['playlistItems'][i]['streams'], medias['media_list'][i]))

        return {
            'id': channel_id,
            'title': pc_json_data['title'],
            'entries': entries,
            '_type': 'playlist',
        }


class LimeLightChannelListIE(LimeLightBaseIE):
    IE_NAME = 'limelight:channel_list'
    _VALID_URL = r'http://link\.videoplatform\.limelight\.com/media/?.*channelListId=(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://link.videoplatform.limelight.com/media/?channelListId=301b117890c4465c8179ede21fd92e2b',
        'info_dict': {
            'id': '301b117890c4465c8179ede21fd92e2b',
            'title': 'Website - Hero Player',
        },
        'playlist_mincount': 2,
    }
    PLAYLIST_SERVICE_URL = 'http://production-ps.lvp.llnw.net/r/PlaylistService/channel_list/%s/%s'

    def _real_extract(self, url):
        channel_list_id = self._match_id(url)

        json_data = self.get_playlist_service(channel_list_id, 'getMobileChannelListById')

        entries = []
        for channel in json_data['channelList']:
            entries.append({
                'url': 'http://link.videoplatform.limelight.com/media/?channelId=%s' % channel['id'],
                '_type': 'url',
                'ie_key': 'LimeLightChannel',
            })

        return {
            'id': channel_list_id,
            'title': json_data['title'],
            'entries': entries,
            '_type': 'playlist',
        }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    smuggle_url,
    unsmuggle_url,
    ExtractorError,
)


class LimelightBaseIE(InfoExtractor):
    _PLAYLIST_SERVICE_URL = 'http://production-ps.lvp.llnw.net/r/PlaylistService/%s/%s/%s'
    _API_URL = 'http://api.video.limelight.com/rest/organizations/%s/%s/%s/%s.json'

    @classmethod
    def _extract_urls(cls, webpage, source_url):
        lm = {
            'Media': 'media',
            'Channel': 'channel',
            'ChannelList': 'channel_list',
        }
        entries = []
        for kind, video_id in re.findall(
                r'LimelightPlayer\.doLoad(Media|Channel|ChannelList)\(["\'](?P<id>[a-z0-9]{32})',
                webpage):
            entries.append(cls.url_result(
                smuggle_url(
                    'limelight:%s:%s' % (lm[kind], video_id),
                    {'source_url': source_url}),
                'Limelight%s' % kind, video_id))
        for mobj in re.finditer(
                # As per [1] class attribute should be exactly equal to
                # LimelightEmbeddedPlayerFlash but numerous examples seen
                # that don't exactly match it (e.g. [2]).
                # 1. http://support.3playmedia.com/hc/en-us/articles/227732408-Limelight-Embedding-the-Captions-Plugin-with-the-Limelight-Player-on-Your-Webpage
                # 2. http://www.sedona.com/FacilitatorTraining2017
                r'''(?sx)
                    <object[^>]+class=(["\'])(?:(?!\1).)*\bLimelightEmbeddedPlayerFlash\b(?:(?!\1).)*\1[^>]*>.*?
                        <param[^>]+
                            name=(["\'])flashVars\2[^>]+
                            value=(["\'])(?:(?!\3).)*(?P<kind>media|channel(?:List)?)Id=(?P<id>[a-z0-9]{32})
                ''', webpage):
            kind, video_id = mobj.group('kind'), mobj.group('id')
            entries.append(cls.url_result(
                smuggle_url(
                    'limelight:%s:%s' % (kind, video_id),
                    {'source_url': source_url}),
                'Limelight%s' % kind.capitalize(), video_id))
        return entries

    def _call_playlist_service(self, item_id, method, fatal=True, referer=None):
        headers = {}
        if referer:
            headers['Referer'] = referer
        try:
            return self._download_json(
                self._PLAYLIST_SERVICE_URL % (self._PLAYLIST_SERVICE_PATH, item_id, method),
                item_id, 'Downloading PlaylistService %s JSON' % method, fatal=fatal, headers=headers)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error = self._parse_json(e.cause.read().decode(), item_id)['detail']['contentAccessPermission']
                if error == 'CountryDisabled':
                    self.raise_geo_restricted()
                raise ExtractorError(error, expected=True)
            raise

    def _call_api(self, organization_id, item_id, method):
        return self._download_json(
            self._API_URL % (organization_id, self._API_PATH, item_id, method),
            item_id, 'Downloading API %s JSON' % method)

    def _extract(self, item_id, pc_method, mobile_method, meta_method, referer=None):
        pc = self._call_playlist_service(item_id, pc_method, referer=referer)
        metadata = self._call_api(pc['orgId'], item_id, meta_method)
        mobile = self._call_playlist_service(item_id, mobile_method, fatal=False, referer=referer)
        return pc, mobile, metadata

    def _extract_info(self, streams, mobile_urls, properties):
        video_id = properties['media_id']
        formats = []
        urls = []
        for stream in streams:
            stream_url = stream.get('url')
            if not stream_url or stream.get('drmProtected') or stream_url in urls:
                continue
            urls.append(stream_url)
            ext = determine_ext(stream_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    stream_url, video_id, f4m_id='hds', fatal=False))
            else:
                fmt = {
                    'url': stream_url,
                    'abr': float_or_none(stream.get('audioBitRate')),
                    'fps': float_or_none(stream.get('videoFrameRate')),
                    'ext': ext,
                }
                width = int_or_none(stream.get('videoWidthInPixels'))
                height = int_or_none(stream.get('videoHeightInPixels'))
                vbr = float_or_none(stream.get('videoBitRate'))
                if width or height or vbr:
                    fmt.update({
                        'width': width,
                        'height': height,
                        'vbr': vbr,
                    })
                else:
                    fmt['vcodec'] = 'none'
                rtmp = re.search(r'^(?P<url>rtmpe?://(?P<host>[^/]+)/(?P<app>.+))/(?P<playpath>mp[34]:.+)$', stream_url)
                if rtmp:
                    format_id = 'rtmp'
                    if stream.get('videoBitRate'):
                        format_id += '-%d' % int_or_none(stream['videoBitRate'])
                    http_format_id = format_id.replace('rtmp', 'http')

                    CDN_HOSTS = (
                        ('delvenetworks.com', 'cpl.delvenetworks.com'),
                        ('video.llnw.net', 's2.content.video.llnw.net'),
                    )
                    for cdn_host, http_host in CDN_HOSTS:
                        if cdn_host not in rtmp.group('host').lower():
                            continue
                        http_url = 'http://%s/%s' % (http_host, rtmp.group('playpath')[4:])
                        urls.append(http_url)
                        if self._is_valid_url(http_url, video_id, http_format_id):
                            http_fmt = fmt.copy()
                            http_fmt.update({
                                'url': http_url,
                                'format_id': http_format_id,
                            })
                            formats.append(http_fmt)
                            break

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
            format_id = mobile_url.get('targetMediaPlatform')
            if not media_url or format_id in ('Widevine', 'SmoothStreaming') or media_url in urls:
                continue
            urls.append(media_url)
            ext = determine_ext(media_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    stream_url, video_id, f4m_id=format_id, fatal=False))
            else:
                formats.append({
                    'url': media_url,
                    'format_id': format_id,
                    'preference': -1,
                    'ext': ext,
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
        for caption in properties.get('captions', []):
            lang = caption.get('language_code')
            subtitles_url = caption.get('url')
            if lang and subtitles_url:
                subtitles.setdefault(lang, []).append({
                    'url': subtitles_url,
                })
        closed_captions_url = properties.get('closed_captions_url')
        if closed_captions_url:
            subtitles.setdefault('en', []).append({
                'url': closed_captions_url,
                'ext': 'ttml',
            })

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
    _VALID_URL = r'''(?x)
                        (?:
                            limelight:media:|
                            https?://
                                (?:
                                    link\.videoplatform\.limelight\.com/media/|
                                    assets\.delvenetworks\.com/player/loader\.swf
                                )
                                \?.*?\bmediaId=
                        )
                        (?P<id>[a-z0-9]{32})
                    '''
    _TESTS = [{
        'url': 'http://link.videoplatform.limelight.com/media/?mediaId=3ffd040b522b4485b6d84effc750cd86',
        'info_dict': {
            'id': '3ffd040b522b4485b6d84effc750cd86',
            'ext': 'mp4',
            'title': 'HaP and the HB Prince Trailer',
            'description': 'md5:8005b944181778e313d95c1237ddb640',
            'thumbnail': r're:^https?://.*\.jpeg$',
            'duration': 144.23,
            'timestamp': 1244136834,
            'upload_date': '20090604',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        # video with subtitles
        'url': 'limelight:media:a3e00274d4564ec4a9b29b9466432335',
        'md5': '2fa3bad9ac321e23860ca23bc2c69e3d',
        'info_dict': {
            'id': 'a3e00274d4564ec4a9b29b9466432335',
            'ext': 'mp4',
            'title': '3Play Media Overview Video',
            'thumbnail': r're:^https?://.*\.jpeg$',
            'duration': 78.101,
            'timestamp': 1338929955,
            'upload_date': '20120605',
            'subtitles': 'mincount:9',
        },
    }, {
        'url': 'https://assets.delvenetworks.com/player/loader.swf?mediaId=8018a574f08d416e95ceaccae4ba0452',
        'only_matching': True,
    }]
    _PLAYLIST_SERVICE_PATH = 'media'
    _API_PATH = 'media'

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        self._initialize_geo_bypass(smuggled_data.get('geo_countries'))

        pc, mobile, metadata = self._extract(
            video_id, 'getPlaylistByMediaId',
            'getMobilePlaylistByMediaId', 'properties',
            smuggled_data.get('source_url'))

        return self._extract_info(
            pc['playlistItems'][0].get('streams', []),
            mobile['mediaList'][0].get('mobileUrls', []) if mobile else [],
            metadata)


class LimelightChannelIE(LimelightBaseIE):
    IE_NAME = 'limelight:channel'
    _VALID_URL = r'''(?x)
                        (?:
                            limelight:channel:|
                            https?://
                                (?:
                                    link\.videoplatform\.limelight\.com/media/|
                                    assets\.delvenetworks\.com/player/loader\.swf
                                )
                                \?.*?\bchannelId=
                        )
                        (?P<id>[a-z0-9]{32})
                    '''
    _TESTS = [{
        'url': 'http://link.videoplatform.limelight.com/media/?channelId=ab6a524c379342f9b23642917020c082',
        'info_dict': {
            'id': 'ab6a524c379342f9b23642917020c082',
            'title': 'Javascript Sample Code',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'http://assets.delvenetworks.com/player/loader.swf?channelId=ab6a524c379342f9b23642917020c082',
        'only_matching': True,
    }]
    _PLAYLIST_SERVICE_PATH = 'channel'
    _API_PATH = 'channels'

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        channel_id = self._match_id(url)

        pc, mobile, medias = self._extract(
            channel_id, 'getPlaylistByChannelId',
            'getMobilePlaylistWithNItemsByChannelId?begin=0&count=-1',
            'media', smuggled_data.get('source_url'))

        entries = [
            self._extract_info(
                pc['playlistItems'][i].get('streams', []),
                mobile['mediaList'][i].get('mobileUrls', []) if mobile else [],
                medias['media_list'][i])
            for i in range(len(medias['media_list']))]

        return self.playlist_result(entries, channel_id, pc['title'])


class LimelightChannelListIE(LimelightBaseIE):
    IE_NAME = 'limelight:channel_list'
    _VALID_URL = r'''(?x)
                        (?:
                            limelight:channel_list:|
                            https?://
                                (?:
                                    link\.videoplatform\.limelight\.com/media/|
                                    assets\.delvenetworks\.com/player/loader\.swf
                                )
                                \?.*?\bchannelListId=
                        )
                        (?P<id>[a-z0-9]{32})
                    '''
    _TESTS = [{
        'url': 'http://link.videoplatform.limelight.com/media/?channelListId=301b117890c4465c8179ede21fd92e2b',
        'info_dict': {
            'id': '301b117890c4465c8179ede21fd92e2b',
            'title': 'Website - Hero Player',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://assets.delvenetworks.com/player/loader.swf?channelListId=301b117890c4465c8179ede21fd92e2b',
        'only_matching': True,
    }]
    _PLAYLIST_SERVICE_PATH = 'channel_list'

    def _real_extract(self, url):
        channel_list_id = self._match_id(url)

        channel_list = self._call_playlist_service(channel_list_id, 'getMobileChannelListById')

        entries = [
            self.url_result('limelight:channel:%s' % channel['id'], 'LimelightChannel')
            for channel in channel_list['channelList']]

        return self.playlist_result(entries, channel_list_id, channel_list['title'])

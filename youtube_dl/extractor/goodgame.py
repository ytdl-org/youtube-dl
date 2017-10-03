# coding=utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError, int_or_none


class GoodgameBaseIE(InfoExtractor):
    _RTMP_SERVER = 'rtmp://46.61.227.158:1940/vod//'
    _API_BASE = 'https://goodgame.ru/api'
    _HLS_BASE = 'https://hls.goodgame.ru/hls'
    _QUALITIES = {
        '240p': '_240',
        '480p': '_480',
        '720p': '_720',
        'Source': ''
    }
    _RE_UPLOADER = r'''(?x)
                        <a[^>]+
                        href=\"https?://(?:www\.)?goodgame\.ru/user/(?P<uploader_id>\d+)/\"
                        [^>]*>
                        (?P<uploader>[^<]+)
                    '''
    _RE_TIMESTAMP = r'utc-timestamp=\"(?P<timestamp>\d+)\"'


class GoodgameStreamIE(GoodgameBaseIE):
    IE_NAME = 'goodgame:stream'
    _VALID_URL = r'https?://(?:www\.)?goodgame\.ru/(channel/|player\?)(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://goodgame.ru/channel/rutony',
        'info_dict': {
            'id': 'rutony',
            'stream_id': '2399',
            'title': 're:^.*',
            'ext': 'mp4',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://goodgame.ru/player?9418',
        'info_dict': {
            'id': 'Artist.the',
            'stream_id': '9418',
            'title': 're:^.*',
            'ext': 'mp4',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://goodgame.ru/channel/BRAT_OK/#autoplay',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        stream_info = next(
            _ for _ in self._download_json('%s/getchannelstatus?id=%s&fmt=json' % (self._API_BASE, video_id),
                                           video_id,
                                           note='Downloading stream JSON').values())

        if stream_info.get('status') == 'Dead':
            raise ExtractorError('%s is offline' % video_id, expected=True)

        # url with player and stream_id
        if stream_info.get('key') == stream_info.get('stream_id'):
            video_id = self._download_json('%s/player?src=%s' % (self._API_BASE, video_id),
                                           video_id,
                                           note='Downloading streamer info JSON').get('streamer_name')

        _id = self._search_regex('src=\"https://goodgame.ru/player\?(?P<id>\d+)\"', stream_info.get('embed'), 'id')
        thumbnails = [{'url': 'https:%s' % stream_info.get('thumb')}]
        formats = []
        for quality, suffix in self._QUALITIES.items():
            formats.append({
                'format_id': quality,
                'url': '%s/%s%s.m3u8' % (self._HLS_BASE, _id, suffix),
                'ext': 'mp4',
                'protocol': 'm3u8'
            })

        return {
            'id': video_id,
            'stream_id': stream_info.get('stream_id'),
            'title': stream_info.get('title'),
            'description': stream_info.get('description'),
            'view_count': int(stream_info.get('viewers')),
            'status': stream_info.get('status'),
            'thumbnails': thumbnails,
            'formats': formats,
            'is_live': True,
        }


class GoodgameVideoIE(GoodgameBaseIE):
    IE_NAME = 'goodgame:video'
    _VALID_URL = r'https?://(?:www\.)?goodgame\.ru/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://goodgame.ru/video/49359/',
        'info_dict': {
            'id': '49359',
            'title': 'GSL Super tournament s2 - день#4(1/2 и Финал!)Pomi',
            'description': '',
            'uploader': 'Pomi',
            'uploader_id': '374',
            'timestamp': 1506862050,
            'upload_date': '20171001',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # Embedded youtube video
        'url': 'https://goodgame.ru/video/49294/',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': 'EihUN4ylsn4',
            'title': 'Шахматы с Бонивуром | Осторожно, мат на стриме! [запись 25.09.17]',
            'description': 're:^Большое спасибо за поддержку трансляций интеллектуального формата\..*',
            'uploader': 'bonivur',
            'uploader_id': '30',
            'timestamp': 1506416377,
            'upload_date': '20170925',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        matches = list(re.finditer(r'<div[^>]+class=\"title\"[^>]*>(?P<title>[^<]+)', webpage))
        title = matches[1].group('title')
        description = self._html_search_regex(r'<div[^>]+class=\"description\"[^>]*>(?P<info>[^\0]*?)</div>',
                                              webpage, 'info')
        timestamp = int_or_none(self._html_search_regex(self._RE_TIMESTAMP, webpage, 'timestamp'))
        uploader_match = re.search(self._RE_UPLOADER, webpage)
        uploader = uploader_match.group('uploader')
        uploader_id = uploader_match.group('uploader_id')

        embed_url = self._html_search_regex(
            r'<iframe[^>]+src="((?:https?:)?//(?:www\.)?youtube\.com/embed[^"]+)"',
            webpage, 'embed URL', default=None)
        if embed_url:
            return {
                '_type': 'url_transparent',
                'url': embed_url,
                'title': title,
                'description': description,
                'timestamp': timestamp,
                'uploader': uploader,
                'uploader_id': uploader_id
            }

        file = self._html_search_regex(r'<param[^>]+name=\"flashvars\"[^>]+value=\"src=(?P<path>[^=\"]+)\"[^>]*>',
                                       webpage, 'path', default=None)
        if file:
            rtmp_url = '%s%s' % (self._RTMP_SERVER, file)
            formats = [{
                'format_id': 'rtmp',
                'url': rtmp_url,
                'protocol': 'rtmp',
                'ext': 'mp4',
            }]

            return {
                'id': video_id,
                'title': title,
                'description': description,
                'timestamp': timestamp,
                'uploader': uploader,
                'uploader_id': uploader_id,
                'formats': formats,
            }

        raise ExtractorError('Video %s was deleted' % video_id, expected=True)


class GoodgameClipIE(GoodgameBaseIE):
    IE_NAME = 'goodgame:clip'
    _VALID_URL = r'https?://(?:www\.)?goodgame\.ru/clip/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://goodgame.ru/clip/397722/',
        'info_dict': {
            'id': '397722',
            'title': 'ЭТО ФИАСКО',
            'uploader': '0x111BA6FA',
            'uploader_id': '1035569',
            'timestamp': 1506975639,
            'upload_date': '20171002',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://goodgame.ru/clip/397155/?from=rec',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        url = self._og_search_video_url(webpage)
        timestamp = int_or_none(self._html_search_regex(self._RE_TIMESTAMP, webpage, 'timestamp'))
        uploader_match = re.search(self._RE_UPLOADER, webpage)
        uploader = uploader_match.group('uploader')
        uploader_id = uploader_match.group('uploader_id')

        formats = [{
            'format_id': 'clip',
            'url': url,
            # http or https extraction
            'protocol': url[:6].rstrip(':/'),
            'ext': 'mp4',
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
        }

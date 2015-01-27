# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_urllib_parse_unquote,
    compat_parse_qs
)
from ..utils import (
    ExtractorError,
    parse_iso8601,
    parse_duration
)

# ref: http://stackoverflow.com/questions/475074/regex-to-parse-or-validate-base64-data
REGEX_BASE64 = r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?'

CST_ZONE = +8  # China Standard Time


class XuiteIE(InfoExtractor):
    _VALID_URL = r'http://vlog.xuite.net/play/(?P<id>%s)(/.*)?' % REGEX_BASE64
    _TESTS = [{
        # Audio
        'url': 'http://vlog.xuite.net/play/RGkzc1ZULTM4NjA5MTQuZmx2',
        'md5': '63a42c705772aa53fd4c1a0027f86adf',
        'info_dict': {
            'id': 'RGkzc1ZULTM4NjA5MTQuZmx2',
            'ext': 'mp3',
            'upload_date': '20110902',
            'uploader_id': '15973816',
            'uploader': '阿能',
            'timestamp': 1314932940,
            'title': '孤單南半球-歐德陽',
            'thumbnail': 're:^https?://.*\.jpg$',
            'categories': ['個人短片'],
            'duration': 247.246
        }
    }, {
        # Audio with alternative form of url
        'url': 'http://vlog.xuite.net/play/S1dDUjdyLTMyOTc3NjcuZmx2/%E5%AD%AB%E7%87%95%E5%A7%BF-%E7%9C%BC%E6%B7%9A%E6%88%90%E8%A9%A9',
        'md5': 'c91645f324de53d82ebb80930e1a73d2',
        'info_dict': {
            'id': 'S1dDUjdyLTMyOTc3NjcuZmx2',
            'ext': 'mp3',
            'upload_date': '20101226',
            'uploader_id': '10102699',
            'uploader': '蠍',
            'timestamp': 1293367080,
            'title': '孫燕姿-眼淚成詩',
            'thumbnail': 're:^https?://.*\.jpg$',
            'categories': ['個人短片'],
            'duration': 223.19
        }
    }, {
        # Video with only one format
        'url': 'http://vlog.xuite.net/play/TkRZNjhULTM0NDE2MjkuZmx2',
        'md5': 'c45737fc8ac5dc8ac2f92ecbcecf505e',
        'info_dict': {
            'id': 'TkRZNjhULTM0NDE2MjkuZmx2',
            'ext': 'mp4',
            'upload_date': '20110306',
            'uploader_id': '10400126',
            'uploader': 'Valen',
            'timestamp': 1299383640,
            'title': '孫燕姿 - 眼淚成詩',
            'thumbnail': 're:^https?://.*\.jpg$',
            'categories': ['影視娛樂'],
            'duration': 217.399
        }
    }, {
        # Video with two formats
        'url': 'http://vlog.xuite.net/play/bWo1N1pLLTIxMzAxMTcwLmZsdg==',
        'md5': '1166e0f461efe55b62e26a2d2a68e6de',
        'info_dict': {
            'id': 'bWo1N1pLLTIxMzAxMTcwLmZsdg==',
            'ext': 'mp4',
            'upload_date': '20150117',
            'uploader_id': '242127761',
            'uploader': '我只是想認真點',
            'timestamp': 1421481240,
            'title': '暗殺教室 02',
            'thumbnail': 're:^https?://.*\.jpg$',
            'categories': ['電玩動漫'],
            'duration': 1384.907
        }
    }]

    def _flv_config(self, media_id):
        base64_media_id = base64.b64encode(media_id.encode('utf-8')).decode('utf-8')
        flv_config_url = 'http://vlog.xuite.net/flash/player?media=' + base64_media_id
        flv_config = self._download_xml(flv_config_url, 'flv config')

        prop_dict = {}
        for prop in flv_config.findall('./property'):
            prop_id = base64.b64decode(prop.attrib['id']).decode('utf-8')

            if not prop.text:
                continue  # CDATA may be empty in flv config

            encoded_content = base64.b64decode(prop.text).decode('utf-8')
            prop_dict[prop_id] = compat_urllib_parse_unquote(encoded_content)

        return prop_dict

    def _type_string(self, media_url):
        query_string = compat_urlparse.urlparse(media_url).query
        type_string = compat_parse_qs(query_string)['q'][0]
        return type_string

    def _guess_ext(self, media_url):
        type_string = self._type_string(media_url)
        if type_string == 'mp3':
            return 'mp3'
        elif type_string == '360' or type_string == '720':
            return 'mp4'
        else:
            raise ExtractorError('Unknown type string %s' % type_string)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(url, video_id)
        media_id = self._html_search_regex(r'data-mediaid="(\d+)"', page, 'media id')
        flv_config = self._flv_config(media_id)

        timestamp_local = parse_iso8601(flv_config['publish_datetime'], ' ')
        timestamp_gmt = timestamp_local - CST_ZONE * 3600

        ret_attrs = {
            'id': video_id,
            'title': flv_config['title'],
            'thumbnail': flv_config['thumb'],
            'uploader': flv_config['author_name'],
            'timestamp': timestamp_gmt,
            'uploader_id': flv_config['author_id'],
            'duration': parse_duration(flv_config['duration']),
            'categories': [flv_config['category']]
        }

        if 'hq_src' in flv_config:
            urls = [flv_config['src'], flv_config['hq_src']]

            ret_attrs['formats'] = []

            for url in urls:
                ret_attrs['formats'].append({
                    'url': url,
                    'ext': self._guess_ext(url),
                    'format_id': self._type_string(url),
                    'height': int(self._type_string(url))
                })
        else:
            ret_attrs['url'] = flv_config['src']
            ret_attrs['ext'] = self._guess_ext(flv_config['src'])

        return ret_attrs

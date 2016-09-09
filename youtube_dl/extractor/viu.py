# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    clean_html,
    sanitized_Request
)
from ..compat import compat_urllib_request


class ViuBaseIE(InfoExtractor):

    @classmethod
    def _get_viu_auth(self):
        viu_auth_url = 'https://www.viu.com/api/apps/v2/authenticate?acct=test&appid=viu_desktop&fmt=json' \
                       '&iid=guest&languageid=default&platform=desktop&userid=guest&useridtype=guest&ver=1.0'
        viu_auth_res = compat_urllib_request.urlopen(viu_auth_url)
        return viu_auth_res.info().get('X-VIU-AUTH')


class ViuIE(ViuBaseIE):
    IE_NAME = 'viu:show'
    _VALID_URL = r'https?://www\.viu\.com/.+/(?:vod|media)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.viu.com/ott/sg/en-us/vod/3421/The%20Prime%20Minister%20and%20I',
        'info_dict': {
            'id': '3421',
            'ext': 'mp4',
            'title': 'The Prime Minister and I - Episode 17',
            'description': 'md5:1e7486a619b6399b25ba6a41c0fe5b2c',
        },
        'params': {
            'skip_download': 'm3u8 download',
            'no_check_certificate': True,
        },
        'skip': 'Geo-restricted to Singapore',
    }, {
        'url': 'http://www.viu.com/ott/hk/zh-hk/vod/7123/%E5%A4%A7%E4%BA%BA%E5%A5%B3%E5%AD%90',
        'info_dict': {
            'id': '7123',
            'ext': 'mp4',
            'title': '大人女子 - Episode 10',
            'description': 'md5:4eb0d8b08cf04fcdc6bbbeb16043434f',
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
        'skip': 'Geo-restricted to Hong Kong',
    }, {
        'url': 'https://www.viu.com/en/media/1116705532?containerId=playlist-22168059',
        'info_dict': {
            'id': '1116705532',
            'ext': 'mp4',
            'title': 'Citizen Khan - Episode 1',
            'description': 'md5:d7ea1604f49e5ba79c212c551ce2110e',
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
        'skip': 'Geo-restricted to India',
    }, {
        'url': 'https://www.viu.com/en/media/1130599965',
        'info_dict': {
            'id': '1130599965',
            'ext': 'mp4',
            'title': 'Jealousy Incarnate - Episode 1',
            'description': 'md5:d3d82375cab969415d2720b6894361e9',
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
        'skip': 'Geo-restricted to Indonesia',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url, video_id, note='Downloading video page')

        mobj = re.search(
            r'<div class=["\']error-title[^<>]+?>(?P<err>.+?)</div>', webpage, flags=re.DOTALL)

        if mobj:
            raise ExtractorError(clean_html(mobj.group('err')), expected=True)

        config_js_url = self._search_regex(
            r'src=(["\'])(?P<api_url>.+?/js/config\.js)(?:\?.+?)?\1', webpage, 'config_js',
            group='api_url', default=None)

        if not config_js_url:
            # content is from ID, IN, MY
            req = sanitized_Request('https://www.viu.com/api/clip/load?appid=viu_desktop&fmt=json&id=' + video_id)
            req.add_header('X-VIU-AUTH', self._get_viu_auth())
            video_info = self._download_json(
                req, video_id, note='Downloading video info').get('response', {}).get('item', [{}])[0]

            formats = self._extract_m3u8_formats(
                video_info['href'], video_id, 'mp4',
                m3u8_id='hls', fatal=False)
            self._sort_formats(formats)

            subtitles = {}
            for key, value in list(video_info.items()):
                mobj = re.match(r'^subtitle_(?P<lang>[^_]+?)_(?P<ext>(vtt|srt))', key)
                if not mobj:
                    continue
                if not subtitles.get(mobj.group('lang')):
                    subtitles[mobj.group('lang')] = []
                subtitles[mobj.group('lang')].append(
                    {'url': value, 'ext': mobj.group('ext')})

            title = '%s - Episode %s' % (video_info['moviealbumshowname'],
                                         video_info.get('episodeno'))
            description = video_info.get('description')
            duration = int_or_none(video_info.get('duration'))
            series = video_info.get('moviealbumshowname')
            episode_title = video_info.get('title')
            episode_num = int_or_none(video_info.get('episodeno'))

            return {
                'id': video_id,
                'title': title,
                'description': description,
                'series': series,
                'episode': episode_title,
                'episode_number': episode_num,
                'duration': duration,
                'formats': formats,
                'subtitles': subtitles,
            }

        # content from HK, SG
        config_js = self._download_webpage(
            'http://www.viu.com' + config_js_url, video_id, note='Downloading config js')
        
        # try to strip away commented code which contains test urls
        config_js = re.sub(r'^//.*?$', '', config_js, flags=re.MULTILINE)
        config_js = re.sub(r'/\*.*?\*/', '', config_js, flags=re.DOTALL)
        
        # Slightly different api_url between HK and SG config.js
        # http://www.viu.com/ott/hk/v1/js/config.js =>  '//www.viu.com/ott/hk/index.php?r='
        # http://www.viu.com/ott/sg/v1/js/config.js => 'http://www.viu.com/ott/sg/index.php?r='
        api_url = self._proto_relative_url(
            self._search_regex(
                r'var\s+api_url\s*=\s*(["\'])(?P<api_url>(?:https?:)?//.+?\?r=)\1',
                config_js, 'api_url', group='api_url'), scheme='http:')

        stream_info_url = self._proto_relative_url(
            self._search_regex(
                r'var\s+video_url\s*=\s*(["\'])(?P<video_url>(?:https?:)?//.+?\?ccs_product_id=)\1',
                config_js, 'video_url', group='video_url'), scheme='http:')

        if url.startswith('https://'):
            api_url = re.sub('^http://', 'https://', api_url)

        video_info = self._download_json(
            api_url + 'vod/ajax-detail&platform_flag_label=web&product_id=' + video_id,
            video_id, note='Downloading video info').get('data', {})

        ccs_product_id = video_info.get('current_product', {}).get('ccs_product_id')

        if not ccs_product_id:
            raise ExtractorError('This video is not available in your region.', expected=True)

        stream_info = self._download_json(
            stream_info_url + ccs_product_id, video_id,
            note='Downloading stream info').get('data', {}).get('stream', {})

        formats = []
        for vid_format, stream_url in stream_info.get('url', {}).items():
            br = int_or_none(self._search_regex(
                r's(?P<br>[0-9]+)p', vid_format, 'bitrate', group='br'))
            formats.append({
                'format_id': vid_format,
                'url': stream_url,
                'vbr': br,
                'ext': 'mp4',
                'filesize': stream_info.get('size', {}).get(vid_format)
            })
        self._sort_formats(formats)

        subtitles = {}
        if video_info.get('current_product', {}).get('subtitle', []):
            for sub in video_info.get('current_product', {}).get('subtitle', []):
                subtitles[sub.get('name')] = [{
                    'url': sub.get('url'),
                    'ext': 'srt',
                }]

        episode_info = next(
            p for p in video_info.get('series', {}).get('product', [])
            if p.get('product_id') == video_id)

        title = '%s - Episode %s' % (video_info.get('series', {}).get('name'),
                                     episode_info.get('number'))
        description = episode_info.get('description')
        thumbnail = episode_info.get('cover_image_url')
        duration = int_or_none(stream_info.get('duration'))
        series = video_info.get('series', {}).get('name')
        episode_title = episode_info.get('synopsis')
        episode_num = int_or_none(episode_info.get('number'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'episode': episode_title,
            'episode_number': episode_num,
            'duration': duration,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }


class ViuPlaylistIE(ViuBaseIE):
    IE_NAME = 'viu:playlist'
    _VALID_URL = r'https?://www\.viu\.com/.+/listing/(?P<id>playlist\-[0-9]+)'
    _TEST = {
        'url': 'https://www.viu.com/en/listing/playlist-22461380',
        'info_dict': {
            'id': 'playlist-22461380',
            'title': 'The Good Wife',
        },
        'playlist_count': 16,
        'skip': 'Geo-restricted to Indonesia',
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        req = sanitized_Request('https://www.viu.com/api/container/load?appid=viu_desktop&fmt=json&id=' + playlist_id)
        req.add_header('X-VIU-AUTH', self._get_viu_auth())
        playlist_info = self._download_json(
            req, playlist_id, note='Downloading playlist info').get('response', {}).get('container')

        name = playlist_info['title']
        entries = [
            self.url_result(
                'https://www.viu.com/en/media/%s' % item['id'],
                'Viu', item['id'])
            for item in playlist_info['item'] if item['id']]

        return self.playlist_result(entries, playlist_id, name)

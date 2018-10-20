# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import js_to_json


class LineTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.line\.me/v/(?P<id>\d+)_[^/]+'

    _TESTS = [{
        'url': 'https://tv.line.me/v/793123_goodbye-mrblack-ep1-1/list/69246',
        'info_dict': {
            'id': '793123',
            'ext': 'mp4',
            'title': 'Goodbye Mr.Black | EP.1-1',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 998.509,
            'view_count': int,
        },
    }, {
        'url': 'https://tv.line.me/v/2587507_%E6%B4%BE%E9%81%A3%E5%A5%B3%E9%86%ABx-ep1-02/list/185245',
        'only_matching': True,
    }, {
        'url': 'https://tv.line.me/v/1730228_%E6%A5%B5%E5%93%81%E7%B5%95%E9%85%8D-%E6%9B%9D%E9%9C%B2%E7%AF%87-%E5%8A%87%E6%83%85%E9%A0%90%E5%91%8A/list/132023',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group('id')
        webpage = self._download_webpage(url, video_id)

        player_params = self._parse_json(self._search_regex(
            r'naver\.WebPlayer\(({[^}]+})\)', webpage, 'player parameters'),
            video_id, transform_source=js_to_json)

        video_info = self._download_json(
            'https://global-nvapis.line.me/linetv/rmcnmv/vod_play_videoInfo.json',
            video_id, query={
                'videoId': player_params['videoId'],
                'key': player_params['key'],
            })

        stream = video_info['streams'][0]
        extra_query = '?__gda__=' + stream['key']['value']
        formats = self._extract_m3u8_formats(
            stream['source'] + extra_query, video_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        for a_format in formats:
            a_format['url'] += extra_query

        duration = None
        for video in video_info.get('videos', {}).get('list', []):
            encoding_option = video.get('encodingOption', {})
            abr = video['bitrate']['audio']
            vbr = video['bitrate']['video']
            tbr = abr + vbr
            formats.append({
                'url': video['source'],
                'format_id': 'http-%d' % int(tbr),
                'height': encoding_option.get('height'),
                'width': encoding_option.get('width'),
                'abr': abr,
                'vbr': vbr,
                'filesize': video.get('size'),
            })
            if video.get('duration') and duration is None:
                duration = video['duration']

        self._sort_formats(formats)

        if not formats[0].get('width'):
            formats[0]['vcodec'] = 'none'

        title = self._og_search_title(webpage)

        # like_count requires an additional API request https://tv.line.me/api/likeit/getCount

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'extra_param_to_segment_url': extra_query[1:],
            'duration': duration,
            'thumbnails': [{'url': thumbnail['source']}
                           for thumbnail in video_info.get('thumbnails', {}).get('list', [])],
            'view_count': video_info.get('meta', {}).get('count'),
        }


class LineTVPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.line\.me/v/(?P<segment>[0-9]+)/list/(?P<id>[0-9]+)'

    _TEST = {
        'url': 'https://tv.line.me/v/1736524/list/132427',
        'info_dict': {
            'id': '132427',
            'title': '極品絕配 EP01'
        },
        'playlist_count': 7,
    }

    def _real_extract(self, url):
        url_re = re.compile(self._VALID_URL)
        m = url_re.match(url)
        playlist_id = m.group('id')
        segment_id = m.group('segment')

        webpage = self._download_webpage(url, playlist_id)
        playlist_title = self._search_regex(
            r'<span[^>]+class="_playlist_name"[^>]*>([^<]+)',
            webpage, 'playlist_title')
        series_title = self._search_regex(
            r"'vpt.title',\s*'([^']+)",
            webpage, 'series_title')

        playlist = self._download_webpage(
            'https://tv.line.me/api/%s/playlist/%s/%s/false/false' % (segment_id, series_title, playlist_id),
            playlist_id)
        segment_paths = re.findall(
            r'<div[^>]+class="vod_item3"[^>]*>[^<]*<a[^>]+href="(/v/[^/]+/list/[^"]+)',
            playlist)
        segment_titles = re.findall(
            r'<tooltip[^>]+title="([^"]+)',
            playlist)

        entries = [
            self.url_result(
                'https://tv.line.me' + segment_path,
                ie='LineTV', video_title=segment_title)
            for segment_path, segment_title in zip(segment_paths, segment_titles)
        ]

        return self.playlist_result(entries, playlist_id, playlist_title)

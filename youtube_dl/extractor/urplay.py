# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class URPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?urplay\.se/program/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://urplay.se/program/190031-tripp-trapp-trad-sovkudde',
        'md5': '15ca67b63fd8fb320ac2bcd854bad7b6',
        'info_dict': {
            'id': '190031',
            'ext': 'mp4',
            'title': 'Tripp, Trapp, Träd : Sovkudde',
            'description': 'md5:b86bffdae04a7e9379d1d7e5947df1d1',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        urplayer_data = self._parse_json(self._search_regex(
            r'urPlayer\.init\(({.+?})\);', webpage, 'urplayer data'), video_id)
        host = self._download_json('http://streaming-loadbalancer.ur.se/loadbalancer.json', video_id)['redirect']

        formats = []
        for quality_attr, quality, preference in (('', 'sd', 0), ('_hd', 'hd', 1)):
            file_rtmp = urplayer_data.get('file_rtmp' + quality_attr)
            if file_rtmp:
                formats.append({
                    'url': 'rtmp://%s/urplay/mp4:%s' % (host, file_rtmp),
                    'format_id': quality + '-rtmp',
                    'ext': 'flv',
                    'preference': preference,
                })
            file_http = urplayer_data.get('file_http' + quality_attr) or urplayer_data.get('file_http_sub' + quality_attr)
            if file_http:
                file_http_base_url = 'http://%s/%s' % (host, file_http)
                formats.extend(self._extract_f4m_formats(
                    file_http_base_url + 'manifest.f4m', video_id,
                    preference, '%s-hds' % quality, fatal=False))
                formats.extend(self._extract_m3u8_formats(
                    file_http_base_url + 'playlist.m3u8', video_id, 'mp4',
                    'm3u8_native', preference, '%s-hls' % quality, fatal=False))
        self._sort_formats(formats)

        subtitles = {}
        for subtitle in urplayer_data.get('subtitles', []):
            subtitle_url = subtitle.get('file')
            kind = subtitle.get('kind')
            if subtitle_url or kind and kind != 'captions':
                continue
            subtitles.setdefault(subtitle.get('label', 'Svenska'), []).append({
                'url': subtitle_url,
            })

        return {
            'id': video_id,
            'title': urplayer_data['title'],
            'description': self._og_search_description(webpage),
            'thumbnail': urplayer_data.get('image'),
            'series': urplayer_data.get('series_title'),
            'subtitles': subtitles,
            'formats': formats,
        }

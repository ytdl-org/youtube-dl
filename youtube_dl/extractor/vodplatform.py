# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unescapeHTML


class VODPlatformIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vod-platform\.net/[eE]mbed/(?P<id>[^/?#]+)'
    _TEST = {
        # from http://www.lbcgroup.tv/watch/chapter/29143/52844/%D8%A7%D9%84%D9%86%D8%B5%D8%B1%D8%A9-%D9%81%D9%8A-%D8%B6%D9%8A%D8%A7%D9%81%D8%A9-%D8%A7%D9%84%D9%80-cnn/ar
        'url': 'http://vod-platform.net/embed/RufMcytHDolTH1MuKHY9Fw',
        'md5': '1db2b7249ce383d6be96499006e951fc',
        'info_dict': {
            'id': 'RufMcytHDolTH1MuKHY9Fw',
            'ext': 'mp4',
            'title': 'LBCi News_ النصرة في ضيافة الـ "سي.أن.أن"',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = unescapeHTML(self._og_search_title(webpage))
        hidden_inputs = self._hidden_inputs(webpage)

        base_url = self._search_regex(
            '(.*/)(?:playlist.m3u8|manifest.mpd)',
            hidden_inputs.get('HiddenmyhHlsLink') or hidden_inputs['HiddenmyDashLink'],
            'base url')
        formats = self._extract_m3u8_formats(
            base_url + 'playlist.m3u8', video_id, 'mp4',
            'm3u8_native', m3u8_id='hls', fatal=False)
        formats.extend(self._extract_mpd_formats(
            base_url + 'manifest.mpd', video_id,
            mpd_id='dash', fatal=False))
        rtmp_formats = self._extract_smil_formats(
            base_url + 'jwplayer.smil', video_id, fatal=False)
        for rtmp_format in rtmp_formats:
            rtsp_format = rtmp_format.copy()
            rtsp_format['url'] = '%s/%s' % (rtmp_format['url'], rtmp_format['play_path'])
            del rtsp_format['play_path']
            del rtsp_format['ext']
            rtsp_format.update({
                'url': rtsp_format['url'].replace('rtmp://', 'rtsp://'),
                'format_id': rtmp_format['format_id'].replace('rtmp', 'rtsp'),
                'protocol': 'rtsp',
            })
            formats.extend([rtmp_format, rtsp_format])
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': hidden_inputs.get('HiddenThumbnail') or self._og_search_thumbnail(webpage),
            'formats': formats,
        }

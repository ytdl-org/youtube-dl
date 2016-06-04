# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class VidioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidio\.com/watch/(?P<id>\d+)-(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015',
        'md5': 'cd2801394afc164e9775db6a140b91fe',
        'info_dict': {
            'id': '165683',
            'display_id': 'dj_ambred-booyah-live-2015',
            'ext': 'mp4',
            'title': 'DJ_AMBRED - Booyah (Live 2015)',
            'description': 'md5:27dc15f819b6a78a626490881adbadf8',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 149,
            'like_count': int,
        },
    }, {
        'url': 'https://www.vidio.com/watch/77949-south-korea-test-fires-missile-that-can-strike-all-of-the-north',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        m3u8_url, duration, thumbnail = [None] * 3

        clips = self._parse_json(
            self._html_search_regex(
                r'data-json-clips\s*=\s*(["\'])(?P<data>\[.+?\])\1',
                webpage, 'video data', default='[]', group='data'),
            display_id, fatal=False)
        if clips:
            clip = clips[0]
            m3u8_url = clip.get('sources', [{}])[0].get('file')
            duration = clip.get('clip_duration')
            thumbnail = clip.get('image')

        m3u8_url = m3u8_url or self._search_regex(
            r'data(?:-vjs)?-clip-hls-url=(["\'])(?P<url>.+?)\1', webpage, 'hls url')
        formats = self._extract_m3u8_formats(m3u8_url, display_id, 'mp4', entry_protocol='m3u8_native')

        duration = int_or_none(duration or self._search_regex(
            r'data-video-duration=(["\'])(?P<duartion>\d+)\1', webpage, 'duration'))
        thumbnail = thumbnail or self._og_search_thumbnail(webpage)

        like_count = int_or_none(self._search_regex(
            (r'<span[^>]+data-comment-vote-count=["\'](\d+)',
             r'<span[^>]+class=["\'].*?\blike(?:__|-)count\b.*?["\'][^>]*>\s*(\d+)'),
            webpage, 'like count', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': thumbnail,
            'duration': duration,
            'like_count': like_count,
            'formats': formats,
        }

# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor

from ..utils import int_or_none


class VidioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidio\.com/watch/(?P<id>\d{6})-(?P<display_id>[^/?]+)'
    _TEST = {
        'url': 'http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015',
        'info_dict': {
            'id': '165683',
            'title': 'DJ_AMBRED - Booyah (Live 2015)',
            'ext': 'mp4',
            'thumbnail': 'https://cdn0-a.production.vidio.static6.com/uploads/video/image/165683/dj_ambred-booyah-live-2015-bfb2ba.jpg',
            'description': 'md5:27dc15f819b6a78a626490881adbadf8',
            'duration': 149, 
        },
        'params': {
            # m3u8 download
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        video_data = self._parse_json(self._html_search_regex(
            r'data-json-clips\s*=\s*"\[(.+)\]"', webpage, 'video data'), display_id)

        formats = self._extract_m3u8_formats(
            video_data['sources'][0]['file'],
            display_id, ext='mp4')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'thumbnail': video_data.get('image'),
            'description': self._og_search_description(webpage),
            'duration': int_or_none(video_data.get('clip_duration')),
        }

# coding: utf-8
from __future__ import unicode_literals

from string import ascii_lowercase
from hashlib import md5

from .common import InfoExtractor
from ..utils import int_or_none
from ..compat import compat_parse_qs


class TrailerAddictIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?traileraddict\.com/(?P<id>.+)'
    _TEST = {
        'url': 'http://www.traileraddict.com/prince-avalanche/trailer',
        'md5': '57e39dbcf4142ceb8e1f242ff423fd71',
        'info_dict': {
            'id': '76184',
            'ext': 'mp4',
            'title': 'Prince Avalanche (2013) Trailer',
            'description': 'Trailer for Prince Avalanche. Two highway road workers spend the summer of 1988 away from their city lives. The isolated landscape becomes a place of misadventure as the men find...',
        }
    }

    def _get_video_info(self, video_id):
        hash_str = ''
        for num in video_id:
            hash_str += ascii_lowercase[int(num)]
        hash_str += video_id
        token = md5(hash_str.encode()).hexdigest()[2:7]
        return compat_parse_qs(self._download_webpage(
            'http://v.traileraddict.com/js/flash/fv-secure.php?tid=%s&token=%s' % (video_id, token),
            video_id))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail_url = self._og_search_thumbnail(webpage)
        embed_url = self._html_search_meta('embedUrl', webpage, 'embed url')
        video_id = self._search_regex('/em[bd]/(\d+)', embed_url, 'video id')

        video_info = self._get_video_info(video_id)

        formats = [{
            'url': video_info['fileurl'][0].strip(),
            'width': int_or_none(video_info.get('vidwidth')[0]),
            'height': int_or_none(video_info.get('vidheight')[0]),
            'format_id': 'sd',
        }]

        if video_info.get('hdurl')[0].startswith('http://'):
            formats.append({
                'url': video_info['hdurl'][0].strip(),
                'width': int_or_none(video_info.get('hd_vidwidth')[0]),
                'height': int_or_none(video_info.get('hd_vidheight')[0]),
                'format_id': 'hd',
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail_url,
            'description': description,
            'formats': formats,
        }

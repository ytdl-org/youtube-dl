# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    remove_end,
    remove_start,
)


class GiphyIE(InfoExtractor):
    _VALID_URL = r'https://(?:i|media)\.giphy\.com/media/(\w+)/|https://giphy\.com/gifs/[^/#?]+-(\w+)(?:[#?]|$)'
    _TESTS = [{
        'url': 'https://media.giphy.com/media/2rj8VysAig8QE/giphy.gif',
        'md5': 'faa04a4e3134cb74005b78b28c34cc29',
        'info_dict': {
            'id': '2rj8VysAig8QE',
            'ext': 'mp4',
            'title': 'Css GIF',
        }
    }, {
        'url': 'https://i.giphy.com/media/oY7zuBsNna7CM/giphy.mp4',
        'only_matching': True
    }, {
        'url': 'https://giphy.com/gifs/quit-playin-MZAvNpYCrFUJi',
        'only_matching': True
    }]

    def _real_extract(self, url):
        [video_id] = filter(None, re.match(self._VALID_URL, url).groups())
        page_url = 'https://media.giphy.com/media/{id}/giphy.gif'.format(id=video_id)
        webpage = self._download_webpage(page_url, video_id)
        title = self._og_search_title(webpage)
        title = remove_end(title, ' - Find & Share on GIPHY')
        formats = []
        for prop in 'image', 'video':
            url = self._og_search_property(prop, webpage)
            mime_type = self._og_search_property(prop + ':type', webpage)
            if mime_type == 'image/gif':
                format_id = 'gif'
                quality = 0
            else:
                format_id = remove_start(mime_type, 'video/')
                quality = 1
            fmt = {
                'url': url,
                'format_id': format_id,
                'quality': quality,
            }
            for dim in 'width', 'height':
                fmt[dim] = int_or_none(
                    self._og_search_property(prop + ':' + dim, webpage, fatal=False))
            formats.append(fmt)
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }

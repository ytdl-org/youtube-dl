# coding: utf-8
from __future__ import unicode_literals

import base64
import re
import xml.etree.ElementTree
import zlib

from .common import InfoExtractor
from ..utils import int_or_none


class VimpleIE(InfoExtractor):
    IE_DESC = 'Vimple.ru'
    _VALID_URL = r'https?://(player.vimple.ru/iframe|vimple.ru)/(?P<id>[a-f0-9]{10,})'
    _TESTS = [
        {
            'url': 'http://vimple.ru/c0f6b1687dcd4000a97ebe70068039cf',
            'md5': '2e750a330ed211d3fd41821c6ad9a279',
            'info_dict': {
                'id': 'c0f6b1687dcd4000a97ebe70068039cf',
                'ext': 'mp4',
                'title': 'Sunset',
                'duration': 20,
                'thumbnail': 're:https?://.*?\.jpg',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        iframe_url = 'http://player.vimple.ru/iframe/%s' % video_id

        iframe = self._download_webpage(
            iframe_url, video_id,
            note='Downloading iframe', errnote='unable to fetch iframe')
        player_url = self._html_search_regex(
            r'"(http://player.vimple.ru/flash/.+?)"', iframe, 'player url')

        player = self._request_webpage(
            player_url, video_id, note='Downloading swf player').read()

        player = zlib.decompress(player[8:])

        xml_pieces = re.findall(b'([a-zA-Z0-9 =+/]{500})', player)
        xml_pieces = [piece[1:-1] for piece in xml_pieces]

        xml_data = b''.join(xml_pieces)
        xml_data = base64.b64decode(xml_data)

        xml_data = xml.etree.ElementTree.fromstring(xml_data)

        video = xml_data.find('Video')
        quality = video.get('quality')
        q_tag = video.find(quality.capitalize())

        formats = [
            {
                'url': q_tag.get('url'),
                'tbr': int(q_tag.get('bitrate')),
                'filesize': int(q_tag.get('filesize')),
                'format_id': quality,
            },
        ]

        return {
            'id': video_id,
            'title': video.find('Title').text,
            'formats': formats,
            'thumbnail': video.find('Poster').get('url'),
            'duration': int_or_none(video.get('duration')),
            'webpage_url': video.find('Share').get('videoPageUrl'),
        }

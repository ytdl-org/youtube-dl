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
        # Quality: Large, from iframe
        {
            'url': 'http://player.vimple.ru/iframe/b132bdfd71b546d3972f9ab9a25f201c',
            'info_dict': {
                'id': 'b132bdfd71b546d3972f9ab9a25f201c',
                'title': 'great-escape-minecraft.flv',
                'ext': 'mp4',
                'duration': 352,
                'webpage_url': 'http://vimple.ru/b132bdfd71b546d3972f9ab9a25f201c',
            },
        },
        # Quality: Medium, from mainpage
        {
            'url': 'http://vimple.ru/a15950562888453b8e6f9572dc8600cd',
            'info_dict': {
                'id': 'a15950562888453b8e6f9572dc8600cd',
                'title': 'DB 01',
                'ext': 'flv',
                'duration': 1484,
                'webpage_url': 'http://vimple.ru/a15950562888453b8e6f9572dc8600cd',
            }
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

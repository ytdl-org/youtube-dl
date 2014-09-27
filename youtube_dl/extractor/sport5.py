# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from youtube_dl.utils import compat_str, compat_urlretrieve



class Sport5IE(InfoExtractor):
    _VALID_URL = r'http://.*sport5\.co\.il'
    _TESTS = [{
            'url': 'http://vod.sport5.co.il/?Vc=147&Vi=176331&Page=1',
            'info_dict': {
                'id': 's5-Y59xx1-GUh2',
                'ext': 'mp4',
                'title': 'md5:4a2a5eba7e7dc88fdc446cbca8a41c79',
            }
        }, {
            'url': 'http://www.sport5.co.il/articles.aspx?FolderID=3075&docID=176372&lang=HE',
            'info_dict': {
                'id': 's5-SiXxx1-hKh2',
                'ext': 'mp4',
                'title': 'md5:5cb1c6bfc0f16086e59f6683013f8e02',
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        webpage = self._download_webpage(url, '')

        media_id = self._html_search_regex('clipId=(s5-\w+-\w+)', webpage, 'media id')

        xml = self._download_xml(
            'http://sport5-metadata-rr-d.nsacdn.com/vod/vod/%s/HDS/metadata.xml' % media_id,
            media_id, 'Downloading media XML')

        title = xml.find('./Title').text
        duration = xml.find('./Duration').text
        description = xml.find('./Description').text
        thumbnail = xml.find('./PosterLinks/PosterIMG').text
        player_url = xml.find('./PlaybackLinks/PlayerUrl').text
        file_els = xml.findall('./PlaybackLinks/FileURL')

        formats = []

        for file_el in file_els:
            bitrate = file_el.attrib.get('bitrate')
            width = int(file_el.attrib.get('width'))
            height = int(file_el.attrib.get('height'))
            formats.append({
                'url': compat_str(file_el.text),
                'ext': 'mp4',
                'height': height,
                'width': width
            })

        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'player_url': player_url,
        }
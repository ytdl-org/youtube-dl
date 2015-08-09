from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    find_xpath_attr,
    int_or_none,
    parse_duration,
    unified_strdate,
)


class VideoLecturesNetIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?videolectures\.net/(?P<id>[^/#?]+)/*(?:[#?].*)?$'
    IE_NAME = 'videolectures.net'

    _TEST = {
        'url': 'http://videolectures.net/promogram_igor_mekjavic_eng/',
        'info_dict': {
            'id': 'promogram_igor_mekjavic_eng',
            'ext': 'mp4',
            'title': 'Automatics, robotics and biocybernetics',
            'description': 'md5:815fc1deb6b3a2bff99de2d5325be482',
            'upload_date': '20130627',
            'duration': 565,
            'thumbnail': 're:http://.*\.jpg',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        smil_url = 'http://videolectures.net/%s/video/1/smil.xml' % video_id
        smil = self._download_xml(smil_url, video_id)

        title = find_xpath_attr(smil, './/meta', 'name', 'title').attrib['content']
        description_el = find_xpath_attr(smil, './/meta', 'name', 'abstract')
        description = (
            None if description_el is None
            else description_el.attrib['content'])
        upload_date = unified_strdate(
            find_xpath_attr(smil, './/meta', 'name', 'date').attrib['content'])

        switch = smil.find('.//switch')
        duration = parse_duration(switch.attrib.get('dur'))
        thumbnail_el = find_xpath_attr(switch, './image', 'type', 'thumbnail')
        thumbnail = (
            None if thumbnail_el is None else thumbnail_el.attrib.get('src'))

        formats = []
        for v in switch.findall('./video'):
            proto = v.attrib.get('proto')
            if proto not in ['http', 'rtmp']:
                continue
            f = {
                'width': int_or_none(v.attrib.get('width')),
                'height': int_or_none(v.attrib.get('height')),
                'filesize': int_or_none(v.attrib.get('size')),
                'tbr': int_or_none(v.attrib.get('systemBitrate')) / 1000.0,
                'ext': v.attrib.get('ext'),
            }
            src = v.attrib['src']
            if proto == 'http':
                if self._is_valid_url(src, video_id):
                    f['url'] = src
                    formats.append(f)
            elif proto == 'rtmp':
                f.update({
                    'url': v.attrib['streamer'],
                    'play_path': src,
                    'rtmp_real_time': True,
                })
                formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'duration': duration,
            'thumbnail': thumbnail,
            'formats': formats,
        }

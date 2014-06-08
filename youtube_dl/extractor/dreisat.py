from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class DreiSatIE(InfoExtractor):
    IE_NAME = '3sat'
    _VALID_URL = r'(?:http://)?(?:www\.)?3sat\.de/mediathek/(?:index\.php)?\?(?:(?:mode|display)=[^&]+&)*obj=(?P<id>[0-9]+)$'
    _TEST = {
        'url': 'http://www.3sat.de/mediathek/index.php?obj=36983',
        'md5': '9dcfe344732808dbfcc901537973c922',
        'info_dict': {
            'id': '36983',
            'ext': 'mp4',
            'title': 'Kaffeeland Schweiz',
            'description': 'md5:cc4424b18b75ae9948b13929a0814033',
            'uploader': '3sat',
            'upload_date': '20130622'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        details_url = 'http://www.3sat.de/mediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        details_doc = self._download_xml(details_url, video_id, 'Downloading video details')

        thumbnail_els = details_doc.findall('.//teaserimage')
        thumbnails = [{
            'width': int(te.attrib['key'].partition('x')[0]),
            'height': int(te.attrib['key'].partition('x')[2]),
            'url': te.text,
        } for te in thumbnail_els]

        information_el = details_doc.find('.//information')
        video_title = information_el.find('./title').text
        video_description = information_el.find('./detail').text

        details_el = details_doc.find('.//details')
        video_uploader = details_el.find('./channel').text
        upload_date = unified_strdate(details_el.find('./airtime').text)

        format_els = details_doc.findall('.//formitaet')
        formats = [{
            'format_id': fe.attrib['basetype'],
            'width': int(fe.find('./width').text),
            'height': int(fe.find('./height').text),
            'url': fe.find('./url').text,
            'filesize': int(fe.find('./filesize').text),
            'video_bitrate': int(fe.find('./videoBitrate').text),
        } for fe in format_els
            if not fe.find('./url').text.startswith('http://www.metafilegenerator.de/')]

        self._sort_formats(formats)

        return {
            '_type': 'video',
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'description': video_description,
            'thumbnails': thumbnails,
            'thumbnail': thumbnails[-1]['url'],
            'uploader': video_uploader,
            'upload_date': upload_date,
        }

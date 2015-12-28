from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
)


class DreiSatIE(InfoExtractor):
    IE_NAME = '3sat'
    _VALID_URL = r'(?:http://)?(?:www\.)?3sat\.de/mediathek/(?:index\.php|mediathek\.php)?\?(?:(?:mode|display)=[^&]+&)*obj=(?P<id>[0-9]+)$'
    _TESTS = [
        {
            'url': 'http://www.3sat.de/mediathek/index.php?mode=play&obj=45918',
            'md5': 'be37228896d30a88f315b638900a026e',
            'info_dict': {
                'id': '45918',
                'ext': 'mp4',
                'title': 'Waidmannsheil',
                'description': 'md5:cce00ca1d70e21425e72c86a98a56817',
                'uploader': '3sat',
                'upload_date': '20140913'
            }
        },
        {
            'url': 'http://www.3sat.de/mediathek/mediathek.php?mode=play&obj=51066',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        details_url = 'http://www.3sat.de/mediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        details_doc = self._download_xml(details_url, video_id, 'Downloading video details')

        status_code = details_doc.find('./status/statuscode')
        if status_code is not None and status_code.text != 'ok':
            code = status_code.text
            if code == 'notVisibleAnymore':
                message = 'Video %s is not available' % video_id
            else:
                message = '%s returned error: %s' % (self.IE_NAME, code)
            raise ExtractorError(message, expected=True)

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

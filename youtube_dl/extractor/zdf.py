# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


def extract_from_xml_url(ie, video_id, xml_url):
    doc = ie._download_xml(
        xml_url, video_id,
        note='Downloading video info',
        errnote='Failed to download video info')

    title = doc.find('.//information/title').text
    description = doc.find('.//information/detail').text
    duration = int(doc.find('.//details/lengthSec').text)
    uploader_node = doc.find('.//details/originChannelTitle')
    uploader = None if uploader_node is None else uploader_node.text
    uploader_id_node = doc.find('.//details/originChannelId')
    uploader_id = None if uploader_id_node is None else uploader_id_node.text
    upload_date = unified_strdate(doc.find('.//details/airtime').text)

    def xml_to_format(fnode):
        video_url = fnode.find('url').text
        is_available = 'http://www.metafilegenerator' not in video_url

        format_id = fnode.attrib['basetype']
        format_m = re.match(r'''(?x)
            (?P<vcodec>[^_]+)_(?P<acodec>[^_]+)_(?P<container>[^_]+)_
            (?P<proto>[^_]+)_(?P<index>[^_]+)_(?P<indexproto>[^_]+)
        ''', format_id)

        ext = format_m.group('container')
        proto = format_m.group('proto').lower()

        quality = fnode.find('./quality').text
        abr = int(fnode.find('./audioBitrate').text) // 1000
        vbr_node = fnode.find('./videoBitrate')
        vbr = None if vbr_node is None else int(vbr_node.text) // 1000

        width_node = fnode.find('./width')
        width = None if width_node is None else int_or_none(width_node.text)
        height_node = fnode.find('./height')
        height = None if height_node is None else int_or_none(height_node.text)

        format_note = ''
        if not format_note:
            format_note = None

        return {
            'format_id': format_id + '-' + quality,
            'url': video_url,
            'ext': ext,
            'acodec': format_m.group('acodec'),
            'vcodec': format_m.group('vcodec'),
            'abr': abr,
            'vbr': vbr,
            'width': width,
            'height': height,
            'filesize': int_or_none(fnode.find('./filesize').text),
            'format_note': format_note,
            'protocol': proto,
            '_available': is_available,
        }

    format_nodes = doc.findall('.//formitaeten/formitaet')
    formats = list(filter(
        lambda f: f['_available'],
        map(xml_to_format, format_nodes)))
    ie._sort_formats(formats)

    return {
        'id': video_id,
        'title': title,
        'description': description,
        'duration': duration,
        'uploader': uploader,
        'uploader_id': uploader_id,
        'upload_date': upload_date,
        'formats': formats,
    }


class ZDFIE(InfoExtractor):
    _VALID_URL = r'^https?://www\.zdf\.de/ZDFmediathek(?P<hash>#)?/(.*beitrag/(?:video/)?)(?P<id>[0-9]+)(?:/[^/?]+)?(?:\?.*)?'

    _TEST = {
        'url': 'http://www.zdf.de/ZDFmediathek/beitrag/video/2037704/ZDFspezial---Ende-des-Machtpokers--?bc=sts;stt',
        'info_dict': {
            'id': '2037704',
            'ext': 'webm',
            'title': 'ZDFspezial - Ende des Machtpokers',
            'description': 'Union und SPD haben sich auf einen Koalitionsvertrag geeinigt. Aber was bedeutet das für die Bürger? Sehen Sie hierzu das ZDFspezial "Ende des Machtpokers - Große Koalition für Deutschland".',
            'duration': 1022,
            'uploader': 'spezial',
            'uploader_id': '225948',
            'upload_date': '20131127',
        },
        'skip': 'Videos on ZDF.de are depublicised in short order',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        xml_url = 'http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        return extract_from_xml_url(self, video_id, xml_url)

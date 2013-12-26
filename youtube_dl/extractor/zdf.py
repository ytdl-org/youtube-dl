# coding: utf-8

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class ZDFIE(InfoExtractor):
    _VALID_URL = r'^https?://www\.zdf\.de/ZDFmediathek(?P<hash>#)?/(.*beitrag/(?:video/)?)(?P<video_id>[0-9]+)(?:/[^/?]+)?(?:\?.*)?'

    _TEST = {
        u"url": u"http://www.zdf.de/ZDFmediathek/beitrag/video/2037704/ZDFspezial---Ende-des-Machtpokers--?bc=sts;stt",
        u"file": u"2037704.webm",
        u"info_dict": {
            u"upload_date": u"20131127",
            u"description": u"Union und SPD haben sich auf einen Koalitionsvertrag geeinigt. Aber was bedeutet das für die Bürger? Sehen Sie hierzu das ZDFspezial \"Ende des Machtpokers - Große Koalition für Deutschland\".",
            u"uploader": u"spezial",
            u"title": u"ZDFspezial - Ende des Machtpokers"
        },
        u"skip": u"Videos on ZDF.de are depublicised in short order",
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        xml_url = u'http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        doc = self._download_xml(
            xml_url, video_id,
            note=u'Downloading video info',
            errnote=u'Failed to download video info')

        title = doc.find('.//information/title').text
        description = doc.find('.//information/detail').text
        uploader_node = doc.find('.//details/originChannelTitle')
        uploader = None if uploader_node is None else uploader_node.text
        duration_str = doc.find('.//details/length').text
        duration_m = re.match(r'''(?x)^
            (?P<hours>[0-9]{2})
            :(?P<minutes>[0-9]{2})
            :(?P<seconds>[0-9]{2})
            (?:\.(?P<ms>[0-9]+)?)
            ''', duration_str)
        duration = (
            (
                (int(duration_m.group('hours')) * 60 * 60) +
                (int(duration_m.group('minutes')) * 60) +
                int(duration_m.group('seconds'))
            )
            if duration_m
            else None
        )
        upload_date = unified_strdate(doc.find('.//details/airtime').text)

        def xml_to_format(fnode):
            video_url = fnode.find('url').text
            is_available = u'http://www.metafilegenerator' not in video_url

            format_id = fnode.attrib['basetype']
            format_m = re.match(r'''(?x)
                (?P<vcodec>[^_]+)_(?P<acodec>[^_]+)_(?P<container>[^_]+)_
                (?P<proto>[^_]+)_(?P<index>[^_]+)_(?P<indexproto>[^_]+)
            ''', format_id)

            ext = format_m.group('container')
            proto = format_m.group('proto').lower()

            quality = fnode.find('./quality').text
            abr = int(fnode.find('./audioBitrate').text) // 1000
            vbr = int(fnode.find('./videoBitrate').text) // 1000

            format_note = u''
            if not format_note:
                format_note = None

            return {
                'format_id': format_id + u'-' + quality,
                'url': video_url,
                'ext': ext,
                'acodec': format_m.group('acodec'),
                'vcodec': format_m.group('vcodec'),
                'abr': abr,
                'vbr': vbr,
                'width': int_or_none(fnode.find('./width').text),
                'height': int_or_none(fnode.find('./height').text),
                'filesize': int_or_none(fnode.find('./filesize').text),
                'format_note': format_note,
                'protocol': proto,
                '_available': is_available,
            }

        format_nodes = doc.findall('.//formitaeten/formitaet')
        formats = list(filter(
            lambda f: f['_available'],
            map(xml_to_format, format_nodes)))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
            'duration': duration,
            'upload_date': upload_date,
        }

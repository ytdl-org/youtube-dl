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


def extract_channel_from_xml_url(ie, channel_id, xml_url):
    doc = ie._download_xml(
        xml_url, channel_id,
        note='Downloading channel info',
        errnote='Failed to download channel info')

    title = doc.find('.//information/title').text
    description = doc.find('.//information/detail').text
    assets = [{'id': asset.find('./details/assetId').text,
               'type': asset.find('./type').text,
               } for asset in doc.findall('.//teasers/teaser')]

    return {
        'id': channel_id,
        'title': title,
        'description': description,
        'assets': assets,
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

    def _extract_video(self, video_id):
        xml_url = 'http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        return extract_from_xml_url(self, video_id, xml_url)

    def _real_extract(self, url):
        return self._extract_video(self._match_id(url))


class ZDFChannelIE(ZDFIE):
    _VALID_URL = r'^https?://www\.zdf\.de/ZDFmediathek(?P<hash>#)?/(.*kanaluebersicht/)(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://www.zdf.de/ZDFmediathek#/kanaluebersicht/1586442/sendung/Titanic',
        'info_dict': {
            'id': '1586442',
            'title': 'Titanic',
            'description': 'md5:444c048cfe3fdc2561be7de4bcbf1d04',
        },
        'playlist_count': 3,
    }

    def _extract_channel(self, channel_id):
        def load_chunks(channel_id, chunk_length):
            offset = 0
            while True:
                url = ('http://www.zdf.de/ZDFmediathek/xmlservice/web/aktuellste?ak=web&offset=%d&maxLength=%d&id=%s'
                       % (offset, chunk_length, channel_id))
                result = extract_channel_from_xml_url(self, channel_id, url)
                yield result
                if len(result['assets']) < chunk_length:
                    return
                offset += chunk_length

        def load_channel(channel_id):
            chunks = list(load_chunks(channel_id, 50))  # The server rejects higher values
            assets = [asset for chunk in chunks for asset in chunk['assets']]
            video_ids = [asset['id'] for asset in
                         filter(lambda asset: asset['type'] == 'video',
                                assets)]
            topic_ids = [asset['id'] for asset in
                         filter(lambda asset: asset['type'] == 'thema',
                                assets)]
            if topic_ids:
                video_ids = reduce(list.__add__,
                                   [load_channel(topic_id)['video_ids']
                                    for topic_id in topic_ids],
                                   video_ids)

            result = chunks[0]
            result['video_ids'] = video_ids
            return result

        channel = load_channel(channel_id)
        return {
            '_type': 'playlist',
            'id': channel['id'],
            'title': channel['title'],
            'description': channel['description'],
            'entries': [self._extract_video(video_id)
                        for video_id in channel['video_ids']],
        }

    def _real_extract(self, url):
        return self._extract_channel(self._match_id(url))

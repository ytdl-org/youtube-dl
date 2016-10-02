# coding: utf-8
from __future__ import unicode_literals

import functools
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    OnDemandPagedList,
    xpath_text,
    determine_ext,
    qualities,
    float_or_none,
    ExtractorError,
)


class ZDFIE(InfoExtractor):
    _VALID_URL = r'(?:zdf:|zdf:video:|https?://www\.zdf\.de/ZDFmediathek(?:#)?/(.*beitrag/(?:video/)?))(?P<id>[0-9]+)(?:/[^/?]+)?(?:\?.*)?'

    _TESTS = [{
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
    }]

    def _parse_smil_formats(self, smil, smil_url, video_id, namespace=None, f4m_params=None, transform_rtmp_url=None):
        param_groups = {}
        for param_group in smil.findall(self._xpath_ns('./head/paramGroup', namespace)):
            group_id = param_group.attrib.get(self._xpath_ns('id', 'http://www.w3.org/XML/1998/namespace'))
            params = {}
            for param in param_group:
                params[param.get('name')] = param.get('value')
            param_groups[group_id] = params

        formats = []
        for video in smil.findall(self._xpath_ns('.//video', namespace)):
            src = video.get('src')
            if not src:
                continue
            bitrate = float_or_none(video.get('system-bitrate') or video.get('systemBitrate'), 1000)
            group_id = video.get('paramGroup')
            param_group = param_groups[group_id]
            for proto in param_group['protocols'].split(','):
                formats.append({
                    'url': '%s://%s' % (proto, param_group['host']),
                    'app': param_group['app'],
                    'play_path': src,
                    'ext': 'flv',
                    'format_id': '%s-%d' % (proto, bitrate),
                    'tbr': bitrate,
                })
        self._sort_formats(formats)
        return formats

    def extract_from_xml_url(self, video_id, xml_url):
        doc = self._download_xml(
            xml_url, video_id,
            note='Downloading video info',
            errnote='Failed to download video info')

        status_code = doc.find('./status/statuscode')
        if status_code is not None and status_code.text != 'ok':
            code = status_code.text
            if code == 'notVisibleAnymore':
                message = 'Video %s is not available' % video_id
            else:
                message = '%s returned error: %s' % (self.IE_NAME, code)
            raise ExtractorError(message, expected=True)

        title = doc.find('.//information/title').text
        description = xpath_text(doc, './/information/detail', 'description')
        duration = int_or_none(xpath_text(doc, './/details/lengthSec', 'duration'))
        uploader = xpath_text(doc, './/details/originChannelTitle', 'uploader')
        uploader_id = xpath_text(doc, './/details/originChannelId', 'uploader id')
        upload_date = unified_strdate(xpath_text(doc, './/details/airtime', 'upload date'))
        subtitles = {}
        captions_url = doc.find('.//caption/url')
        if captions_url is not None:
            subtitles['de'] = [{
                'url': captions_url.text,
                'ext': 'ttml',
            }]

        def xml_to_thumbnails(fnode):
            thumbnails = []
            for node in fnode:
                thumbnail_url = node.text
                if not thumbnail_url:
                    continue
                thumbnail = {
                    'url': thumbnail_url,
                }
                if 'key' in node.attrib:
                    m = re.match('^([0-9]+)x([0-9]+)$', node.attrib['key'])
                    if m:
                        thumbnail['width'] = int(m.group(1))
                        thumbnail['height'] = int(m.group(2))
                thumbnails.append(thumbnail)
            return thumbnails

        thumbnails = xml_to_thumbnails(doc.findall('.//teaserimages/teaserimage'))

        format_nodes = doc.findall('.//formitaeten/formitaet')
        quality = qualities(['veryhigh', 'high', 'med', 'low'])

        def get_quality(elem):
            return quality(xpath_text(elem, 'quality'))
        format_nodes.sort(key=get_quality)
        format_ids = []
        formats = []
        for fnode in format_nodes:
            video_url = fnode.find('url').text
            is_available = 'http://www.metafilegenerator' not in video_url
            if not is_available:
                continue
            format_id = fnode.attrib['basetype']
            quality = xpath_text(fnode, './quality', 'quality')
            format_m = re.match(r'''(?x)
                (?P<vcodec>[^_]+)_(?P<acodec>[^_]+)_(?P<container>[^_]+)_
                (?P<proto>[^_]+)_(?P<index>[^_]+)_(?P<indexproto>[^_]+)
            ''', format_id)

            ext = determine_ext(video_url, None) or format_m.group('container')
            if ext not in ('smil', 'f4m', 'm3u8'):
                format_id = format_id + '-' + quality
            if format_id in format_ids:
                continue

            if ext == 'meta':
                continue
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    video_url, video_id, fatal=False))
            elif ext == 'm3u8':
                # the certificates are misconfigured (see
                # https://github.com/rg3/youtube-dl/issues/8665)
                if video_url.startswith('https://'):
                    continue
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    video_url, video_id, f4m_id=format_id, fatal=False))
            else:
                proto = format_m.group('proto').lower()

                abr = int_or_none(xpath_text(fnode, './audioBitrate', 'abr'), 1000)
                vbr = int_or_none(xpath_text(fnode, './videoBitrate', 'vbr'), 1000)

                width = int_or_none(xpath_text(fnode, './width', 'width'))
                height = int_or_none(xpath_text(fnode, './height', 'height'))

                filesize = int_or_none(xpath_text(fnode, './filesize', 'filesize'))

                format_note = ''
                if not format_note:
                    format_note = None

                formats.append({
                    'format_id': format_id,
                    'url': video_url,
                    'ext': ext,
                    'acodec': format_m.group('acodec'),
                    'vcodec': format_m.group('vcodec'),
                    'abr': abr,
                    'vbr': vbr,
                    'width': width,
                    'height': height,
                    'filesize': filesize,
                    'format_note': format_note,
                    'protocol': proto,
                    '_available': is_available,
                })
            format_ids.append(format_id)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnails': thumbnails,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'formats': formats,
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        xml_url = 'http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id=%s' % video_id
        return self.extract_from_xml_url(video_id, xml_url)


class ZDFChannelIE(InfoExtractor):
    _VALID_URL = r'(?:zdf:topic:|https?://www\.zdf\.de/ZDFmediathek(?:#)?/.*kanaluebersicht/(?:[^/]+/)?)(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.zdf.de/ZDFmediathek#/kanaluebersicht/1586442/sendung/Titanic',
        'info_dict': {
            'id': '1586442',
        },
        'playlist_count': 3,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/meist-gesehen/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/_/1798716?bc=nrt;nrm?flash=off',
        'only_matching': True,
    }]
    _PAGE_SIZE = 50

    def _fetch_page(self, channel_id, page):
        offset = page * self._PAGE_SIZE
        xml_url = (
            'http://www.zdf.de/ZDFmediathek/xmlservice/web/aktuellste?ak=web&offset=%d&maxLength=%d&id=%s'
            % (offset, self._PAGE_SIZE, channel_id))
        doc = self._download_xml(
            xml_url, channel_id,
            note='Downloading channel info',
            errnote='Failed to download channel info')

        title = doc.find('.//information/title').text
        description = doc.find('.//information/detail').text
        for asset in doc.findall('.//teasers/teaser'):
            a_type = asset.find('./type').text
            a_id = asset.find('./details/assetId').text
            if a_type not in ('video', 'topic'):
                continue
            yield {
                '_type': 'url',
                'playlist_title': title,
                'playlist_description': description,
                'url': 'zdf:%s:%s' % (a_type, a_id),
            }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        entries = OnDemandPagedList(
            functools.partial(self._fetch_page, channel_id), self._PAGE_SIZE)

        return {
            '_type': 'playlist',
            'id': channel_id,
            'entries': entries,
        }

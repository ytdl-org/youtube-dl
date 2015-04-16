# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import (
    determine_ext,
    parse_iso8601,
    xpath_text,
)


class SrfIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.srf\.ch/play(?:er)?/tv/[^/]+/video/(?P<display_id>[^?]+)\?id=|tp\.srgssr\.ch/p/flash\?urn=urn:srf:ais:video:)(?P<id>[0-9a-f\-]{36})'
    _TESTS = [{
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '4cd93523723beff51bb4bee974ee238d',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'display_id': 'snowden-beantragt-asyl-in-russland',
            'ext': 'm4v',
            'upload_date': '20130701',
            'title': 'Snowden beantragt Asyl in Russland',
            'timestamp': 1372713995,
        }
    }, {
        # No Speichern (Save) button
        'url': 'http://www.srf.ch/play/tv/top-gear/video/jaguar-xk120-shadow-und-tornado-dampflokomotive?id=677f5829-e473-4823-ac83-a1087fe97faa',
        'md5': 'd97e236e80d1d24729e5d0953d276a4f',
        'info_dict': {
            'id': '677f5829-e473-4823-ac83-a1087fe97faa',
            'display_id': 'jaguar-xk120-shadow-und-tornado-dampflokomotive',
            'ext': 'flv',
            'upload_date': '20130710',
            'title': 'Jaguar XK120, Shadow und Tornado-Dampflokomotive',
            'timestamp': 1373493600,
        },
    }, {
        'url': 'http://www.srf.ch/player/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'only_matching': True,
    }, {
        'url': 'https://tp.srgssr.ch/p/flash?urn=urn:srf:ais:video:28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        display_id = re.match(self._VALID_URL, url).group('display_id') or video_id

        video_data = self._download_xml(
            'http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.xml' % video_id,
            display_id)

        title = xpath_text(
            video_data, './AssetMetadatas/AssetMetadata/title', fatal=True)
        thumbnails = [{
            'url': s.text
        } for s in video_data.findall('.//ImageRepresentation/url')]
        timestamp = parse_iso8601(xpath_text(video_data, './createdDate'))
        # The <duration> field in XML is different from the exact duration, skipping

        formats = []
        for item in video_data.findall('./Playlists/Playlist') + video_data.findall('./Downloads/Download'):
            for url_node in item.findall('url'):
                quality = url_node.attrib['quality']
                full_url = url_node.text
                original_ext = determine_ext(full_url)
                format_id = '%s-%s' % (quality, item.attrib['protocol'])
                if original_ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        full_url + '?hdcore=3.4.0', display_id, f4m_id=format_id))
                elif original_ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        full_url, display_id, 'mp4', m3u8_id=format_id))
                else:
                    formats.append({
                        'url': full_url,
                        'ext': original_ext,
                        'format_id': format_id,
                        'quality': 0 if 'HD' in quality else -1,
                        'preference': 1,
                    })

        self._sort_formats(formats)

        subtitles = {}
        subtitles_data = video_data.find('Subtitles')
        if subtitles_data is not None:
            subtitles_list = [{
                'url': sub.text,
                'ext': determine_ext(sub.text),
            } for sub in subtitles_data]
            if subtitles_list:
                subtitles['de'] = subtitles_list

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'title': title,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'subtitles': subtitles,
        }

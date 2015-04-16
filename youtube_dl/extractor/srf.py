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
    _VALID_URL = r'http://www\.srf\.ch/play(?:er)?/tv/[^/]+/video/(?P<display_id>[^?]+)\?id=(?P<id>[0-9a-f\-]{36})'
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
        'info_dict': {
            'id': '677f5829-e473-4823-ac83-a1087fe97faa',
            'display_id': 'jaguar-xk120-shadow-und-tornado-dampflokomotive',
            'ext': 'mp4',
            'upload_date': '20130710',
            'title': 'Jaguar XK120, Shadow und Tornado-Dampflokomotive',
            'timestamp': 1373493600,
        },
        'params': {
            # Require ffmpeg/avconv
            'skip_download': True,
        }
    }, {
        'url': 'http://www.srf.ch/player/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_xml(
            'http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.xml' % video_id,
            video_id)

        display_id = re.match(self._VALID_URL, url).group('display_id')
        title = xpath_text(
            video_data, './AssetMetadatas/AssetMetadata/title', fatal=True)
        thumbnails = [{
            'url': s.text
        } for s in video_data.findall('.//ImageRepresentation/url')]
        timestamp = parse_iso8601(xpath_text(video_data, './createdDate'))
        # The <duration> field in XML is different from the exact duration, skipping

        formats = []
        for item in video_data.findall('./Playlists/Playlist') + video_data.findall('./Downloads/Download'):
            url_node = item.find('url')
            quality = url_node.attrib['quality']
            full_url = url_node.text
            original_ext = determine_ext(full_url)
            if original_ext == 'f4m':
                full_url += '?hdcore=3.4.0'  # Without this, you get a 403 error
            formats.append({
                'url': full_url,
                'ext': 'mp4' if original_ext == 'm3u8' else original_ext,
                'format_id': '%s-%s' % (quality, item.attrib['protocol']),
                'preference': 0 if 'HD' in quality else -1,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'title': title,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
        }

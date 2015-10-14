# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    qualities,
)


class SRGSSRIE(InfoExtractor):
    _VALID_URL = r'(?:https?://tp\.srgssr\.ch/p(?:/[^/]+)+\?urn=urn|srgssr):(?P<bu>srf|rts|rsi|rtr|swi):(?:[^:]+:)?(?P<type>video|audio):(?P<id>[0-9a-f\-]{36}|\d+)'

    _ERRORS = {
        'AGERATING12': 'To protect children under the age of 12, this video is only available between 8 p.m. and 6 a.m.',
        'AGERATING18': 'To protect children under the age of 18, this video is only available between 11 p.m. and 5 a.m.',
#        'ENDDATE': 'For legal reasons, this video was only available for a specified period of time.',
        'GEOBLOCK': 'For legal reasons, this video is only available in Switzerland.',
        'LEGAL': 'The video cannot be transmitted for legal reasons.',
        'STARTDATE': 'This video is not yet available. Please try again later.',
    }

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()

        media_data = self._download_json(
            'http://il.srgssr.ch/integrationlayer/1.0/ue/%s/%s/play/%s.json' % (bu, media_type, media_id),
            media_id)[media_type.capitalize()]

        if media_data.get('block') and media_data['block'] in self._ERRORS:
            raise ExtractorError(
                    '%s said: %s' % (
                        self.IE_NAME,
                        self._ERRORS[media_data['block']]),
                    expected=True)

        metadata = media_data['AssetMetadatas']['AssetMetadata'][0]
        title = metadata['title']
        description = metadata.get('description')
        created_date = media_data.get('createdDate') or metadata.get('createdDate')
        timestamp = parse_iso8601(created_date)

        thumbnails = []
        if 'Image' in media_data:
            for image in media_data['Image']['ImageRepresentations']['ImageRepresentation']:
                thumbnails.append({
                    'id': image.get('id'),
                    'url': image['url'],
                })

        preference = qualities(['LQ', 'MQ', 'SD', 'HQ', 'HD'])
        formats = []
        for source in media_data['Playlists']['Playlist']:
            assets = {}
            protocol = source.get('@protocol')
            if protocol in ('HTTP-HDS', 'HTTP-HLS'):
                for quality in source['url']:
                    assets[quality['@quality']] = quality['text']
                asset_url = assets.get('HD') or assets.get('HQ') or assets.get('SD') or assets.get('MQ') or assets.get('LQ')
                if '.f4m' in asset_url:
                    formats.extend(self._extract_f4m_formats(asset_url + '?hdcore=3.4.0', media_id, f4m_id='hds'))
                elif '.m3u8' in asset_url:
                    formats.extend(self._extract_m3u8_formats(asset_url, media_id, m3u8_id='hls'))
            else:
                for asset in source['url']:
                    asset_url = asset['text']
                    ext = None
                    if asset_url.startswith('rtmp'):
                        ext = self._search_regex(r'([a-z0-9]+):[^/]+', asset_url, 'ext')
                    formats.append({
                        'format_id': asset['@quality'],
                        'url': asset_url,
                        'preference': preference(asset['@quality']),
                        'ext': ext,
                    })

        if 'Downloads' in media_data:
            for source in media_data['Downloads']['Download']:
                for asset in source['url']:
                    formats.append({
                        'format_id': asset['@quality'],
                        'url': asset['text'],
                        'preference': preference(asset['@quality'])
                    })
        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'formats': formats,
        }


class SRGSSRPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|play)\.)?(?P<bu>srf|rts|rsi|rtr|swissinfo)\.ch/play/(?:tv|radio)/[^/]+/(?P<type>video|audio)/[^?]+\?id=(?P<id>[0-9a-f\-]{36}|\d+)'

    _TESTS = [{
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '4cd93523723beff51bb4bee974ee238d',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'ext': 'm4v',
            'upload_date': '20130701',
            'title': 'Snowden beantragt Asyl in Russland',
            'timestamp': 1372713995,
        }
    }, {
        # No Speichern (Save) button
        'url': 'http://www.srf.ch/play/tv/top-gear/video/jaguar-xk120-shadow-und-tornado-dampflokomotive?id=677f5829-e473-4823-ac83-a1087fe97faa',
        'md5': '0a274ce38fda48c53c01890651985bc6',
        'info_dict': {
            'id': '677f5829-e473-4823-ac83-a1087fe97faa',
            'ext': 'flv',
            'upload_date': '20130710',
            'title': 'Jaguar XK120, Shadow und Tornado-Dampflokomotive',
            'description': 'md5:88604432b60d5a38787f152dec89cd56',
            'timestamp': 1373493600,
        },
    },{
        'url': 'http://www.rtr.ch/play/radio/actualitad/audio/saira-tujetsch-tuttina-cuntinuar-cun-sedrun-muster-turissem?id=63cb0778-27f8-49af-9284-8c7a8c6d15fc',
        'info_dict': {
            'id': '63cb0778-27f8-49af-9284-8c7a8c6d15fc',
            'ext': 'mp3',
            'upload_date': '20151013',
            'title': 'Saira: Tujetsch - tuttina cuntinuar cun Sedrun Mustér Turissem',
            'timestamp': 1444750398,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        return self.url_result('srgssr:%s:%s:%s' % (bu[:3], media_type, media_id), 'SRGSSR')

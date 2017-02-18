# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
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
        # 'ENDDATE': 'For legal reasons, this video was only available for a specified period of time.',
        'GEOBLOCK': 'For legal reasons, this video is only available in Switzerland.',
        'LEGAL': 'The video cannot be transmitted for legal reasons.',
        'STARTDATE': 'This video is not yet available. Please try again later.',
    }

    def _get_tokenized_src(self, url, video_id, format_id):
        sp = compat_urllib_parse_urlparse(url).path.split('/')
        token = self._download_json(
            'http://tp.srgssr.ch/akahd/token?acl=/%s/%s/*' % (sp[1], sp[2]),
            video_id, 'Downloading %s token' % format_id, fatal=False) or {}
        auth_params = token.get('token', {}).get('authparams')
        if auth_params:
            url += '?' + auth_params
        return url

    def get_media_data(self, bu, media_type, media_id):
        media_data = self._download_json(
            'http://il.srgssr.ch/integrationlayer/1.0/ue/%s/%s/play/%s.json' % (bu, media_type, media_id),
            media_id)[media_type.capitalize()]

        if media_data.get('block') and media_data['block'] in self._ERRORS:
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, self._ERRORS[media_data['block']]), expected=True)
        return media_data

    def _extract_subtitles(self, bu, media_data):
        subtitles = {}
        langs = {
            'srf': 'deu',
            'rts': 'fra',
            'rsi': 'ita',
            'rtr': 'roh',
            'swi': 'eng',
        }
        subtitle_data = media_data.get('Subtitles')
        formats = [{'ext': 'ttml', 'urltag': 'TTMLUrl'},
                   {'ext': 'vtt', 'urltag': 'VTTUrl'}]
        subformats = [{'ext': form['ext'], 'url': subtitle_data[form['urltag']]}
                      for form in formats if subtitle_data and subtitle_data.get(form['urltag'])]
        for subform in subformats:
            subtitles.setdefault(langs[bu], []).append(subform)
        return subtitles

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()

        media_data = self.get_media_data(bu, media_type, media_id)

        metadata = media_data['AssetMetadatas']['AssetMetadata'][0]
        title = metadata['title']
        description = metadata.get('description')
        created_date = media_data.get('createdDate') or metadata.get('createdDate')
        timestamp = parse_iso8601(created_date)

        thumbnails = [{
            'id': image.get('id'),
            'url': image['url'],
        } for image in media_data.get('Image', {}).get('ImageRepresentations', {}).get('ImageRepresentation', [])]

        subtitles = self._extract_subtitles(bu, media_data)

        preference = qualities(['LQ', 'MQ', 'SD', 'HQ', 'HD'])
        formats = []
        for source in media_data.get('Playlists', {}).get('Playlist', []) + media_data.get('Downloads', {}).get('Download', []):
            protocol = source.get('@protocol')
            for asset in source['url']:
                asset_url = asset['text']
                quality = asset['@quality']
                format_id = '%s-%s' % (protocol, quality)
                if protocol.startswith('HTTP-HDS') or protocol.startswith('HTTP-HLS'):
                    asset_url = self._get_tokenized_src(asset_url, media_id, format_id)
                    if protocol.startswith('HTTP-HDS'):
                        formats.extend(self._extract_f4m_formats(
                            asset_url + ('?' if '?' not in asset_url else '&') + 'hdcore=3.4.0',
                            media_id, f4m_id=format_id, fatal=False))
                    elif protocol.startswith('HTTP-HLS'):
                        formats.extend(self._extract_m3u8_formats(
                            asset_url, media_id, 'mp4', 'm3u8_native',
                            m3u8_id=format_id, fatal=False))
                else:
                    formats.append({
                        'format_id': format_id,
                        'url': asset_url,
                        'preference': preference(quality),
                        'ext': 'flv' if protocol == 'RTMP' else None,
                    })
        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'formats': formats,
        }


class SRGSSRPlayIE(InfoExtractor):
    IE_DESC = 'srf.ch, rts.ch, rsi.ch, rtr.ch and swissinfo.ch play sites'
    _VALID_URL = r'https?://(?:(?:www|play)\.)?(?P<bu>srf|rts|rsi|rtr|swissinfo)\.ch/play/(?:tv|radio)/[^/]+/(?P<type>video|audio)/[^?]+\?id=(?P<id>[0-9a-f\-]{36}|\d+)'

    _TESTS = [{
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': 'da6b5b3ac9fa4761a942331cef20fcb3',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'ext': 'mp4',
            'upload_date': '20130701',
            'title': 'Snowden beantragt Asyl in Russland',
            'timestamp': 1372713995,
            'subtitles': {},
        }
    }, {
        # No Speichern (Save) button
        'url': 'http://www.srf.ch/play/tv/wort-zum-sonntag/video/vorsaetzlich-gross-denken?id=a2d82e8a-1916-4c29-aade-eec0930ceeeb',
        'md5': '4fd7f008e7cb03f876f50db2fcd7ffcc',
        'info_dict': {
            'id': 'a2d82e8a-1916-4c29-aade-eec0930ceeeb',
            'ext': 'mp4',
            'upload_date': '20170107',
            'title': 'Vorsätzlich gross denken',
            'description': 'Das Wort zum Sonntag spricht der römisch-katholische Theologe Arnold Landtwing.',
            'timestamp': 1483815898,
            'subtitles': {
                'deu': [{'ext': 'ttml', 'url': 'https://ws.srf.ch/subtitles/urn:srf:ais:video:a2d82e8a-1916-4c29-aade-eec0930ceeeb/subtitle.ttml'},
                        {'ext': 'vtt', 'url': 'https://ws.srf.ch/subtitles/urn:srf:ais:video:a2d82e8a-1916-4c29-aade-eec0930ceeeb/subtitle.vtt'}]
            }
        }
    }, {
        'url': 'http://www.srf.ch/play/tv/rundschau/video/wundermittel-olympia-jon-pult-pistole-im-anschlag-eu-zittert-vor-le-pen?id=b664a25c-8ec1-4904-885d-dd9e140ca245',
        'md5': '734dafee62eb8c03ad7e7969799f55fc',
        'info_dict': {
            'id': 'b664a25c-8ec1-4904-885d-dd9e140ca245',
            'ext': 'mp4',
            'upload_date': '20170104',
            'title': 'Wundermittel Olympia, Jon Pult, Pistole im Anschlag, EU zittert vor Le Pen',
            'description': 'Wundermittel Olympia soll Winter-Tourismus retten/ Jon Pult / Pistole im Anschlag: Schweizer decken sich mit Waffen ein / Europa zittert: Frankreich steht vor radikalem Neuanfang',
            'timestamp': 1483562845,
            'subtitles': {
                'deu': [{'ext': 'ttml', 'url': 'https://ws.srf.ch/subtitles/urn:srf:ais:video:b664a25c-8ec1-4904-885d-dd9e140ca245/subtitle.ttml'},
                        {'ext': 'vtt', 'url': 'https://ws.srf.ch/subtitles/urn:srf:ais:video:b664a25c-8ec1-4904-885d-dd9e140ca245/subtitle.vtt'}]
            }
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'http://www.rsi.ch/play/tv/telegiornale/video/telegiornale?id=8500627',
        'md5': 'cb6c9b6bd3ce667e826ca20c0b8f0390',
        'info_dict': {
            'id': '8500627',
            'ext': 'mp4',
            'upload_date': '20170108',
            'title': 'Telegiornale',
            'description': '',
            'timestamp': 1483902000,
            'subtitles': {
                'ita': [{'ext': 'ttml', 'url': 'https://cdn.rsi.ch/subtitles/subt_web/rsi/production/2017/ts_20170108_i_8550811.xml'}]
            }
        },
        'params': {
            'skip_download': True,
        }
    }, {
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
    }, {
        'url': 'http://www.rts.ch/play/tv/-/video/le-19h30?id=6348260',
        'md5': '67a2a9ae4e8e62a68d0e9820cc9782df',
        'info_dict': {
            'id': '6348260',
            'display_id': '6348260',
            'ext': 'mp4',
            'duration': 1796,
            'title': 'Le 19h30',
            'description': '',
            'uploader': '19h30',
            'upload_date': '20141201',
            'timestamp': 1417458600,
            'thumbnail': r're:^https?://.*\.image',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        # other info can be extracted from url + '&layout=json'
        return self.url_result('srgssr:%s:%s:%s' % (bu[:3], media_type, media_id), 'SRGSSR')

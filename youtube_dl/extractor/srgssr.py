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
    _GEO_BYPASS = False
    _GEO_COUNTRIES = ['CH']

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
            'https://tp.srgssr.ch/akahd/token?acl=/%s/%s/*' % (sp[1], sp[2]),
            video_id, 'Downloading %s token' % format_id, fatal=False) or {}
        auth_params = token.get('token', {}).get('authparams')
        if auth_params:
            url += '?' + auth_params
        return url

    def get_media_data(self, bu, media_type, media_id):
        media_data = self._download_json(
            'https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:%s:%s:%s.json' % (bu, media_type, media_id),
            media_id)

        # Look for a chapter media_id
        for chapter in media_data.get('chapterList', []):
            if chapter['id'] == media_id:
                media_data['_chapter'] = chapter
            # Look for a segment media_id
            for segment in chapter.get('segmentList', []):
                if segment['id'] == media_id:
                    media_data['_chapter'] = chapter
                    media_data['_segment'] = segment

        chapter = media_data.get('_chapter', {})
        if chapter.get('blockReason') and chapter['blockReason'] in self._ERRORS:
            message = self._ERRORS[chapter['blockReason']]
            if chapter['blockReason'] == 'GEOBLOCK':
                self.raise_geo_restricted(
                    msg=message, countries=self._GEO_COUNTRIES)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, message), expected=True)

        return media_data

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()

        media_data = self.get_media_data(bu, media_type, media_id)

        chapter = media_data.get('_chapter', {})
        if media_data.get('_segment'):
            metadata = media_data['_segment']
        else:
            metadata = chapter

        title = metadata.get('title')
        description = metadata.get('description', '')
        created_date = metadata.get('date')
        timestamp = parse_iso8601(created_date)

        thumbnails = [{
            'id': chapter.get('id'),
            'url': chapter['imageUrl'],
        }]

        preference = qualities(['LQ', 'MQ', 'SD', 'HQ', 'HD'])
        formats = []
        for resource in chapter.get('resourceList', []):
            asset_url = resource['url']
            protocol = resource['protocol']
            quality = resource['quality']
            asset_pref = preference(quality) * 2
            # Prefer HTTPS transport if available in the same quality
            scheme = compat_urllib_parse_urlparse(asset_url).scheme
            if scheme == 'https':
                asset_pref += 1
            format_id = '%s-%s-%s' % (protocol, quality, scheme.upper())
            asset_url = self._get_tokenized_src(asset_url, media_id, format_id)
            if protocol == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    asset_url + ('?' if '?' not in asset_url else '&') + 'hdcore=3.4.0',
                    media_id, f4m_id=format_id, fatal=False, preference=asset_pref))
            elif protocol == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    asset_url, media_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False, preference=asset_pref))
            else:
                formats.append({
                    'format_id': format_id,
                    'url': asset_url,
                    'preference': asset_pref,
                    'ext': 'flv' if protocol == 'RTMP' else None,
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
    IE_DESC = 'srf.ch, rts.ch, rsi.ch, rtr.ch and swissinfo.ch play sites'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:(?:www|play)\.)?
                        (?P<bu>srf|rts|rsi|rtr|swissinfo)\.ch/play/(?:tv|radio)/
                        (?:
                            [^/]+/(?P<type>video|audio)/[^?]+|
                            popup(?P<type_2>video|audio)player
                        )
                        \?id=(?P<id>[0-9a-f\-]{36}|\d+)
                    '''

    _TESTS = [{
        'url': 'https://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '9a3d59e0afb444e8379bd2685923b9f4',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'ext': 'mp4',
            'upload_date': '20130701',
            'title': 'Snowden beantragt Asyl in Russland',
            'timestamp': 1372708215,
        }
    }, {
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '9a3d59e0afb444e8379bd2685923b9f4',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'ext': 'mp4',
            'upload_date': '20130701',
            'title': 'Snowden beantragt Asyl in Russland',
            'timestamp': 1372708215,
        }
    }, {
        'url': 'http://www.rtr.ch/play/radio/actualitad/audio/saira-tujetsch-tuttina-cuntinuar-cun-sedrun-muster-turissem?id=63cb0778-27f8-49af-9284-8c7a8c6d15fc',
        'info_dict': {
            'id': '63cb0778-27f8-49af-9284-8c7a8c6d15fc',
            'ext': 'mp3',
            'upload_date': '20151013',
            'title': 'Saira: Tujetsch - tuttina cuntinuar cun Sedrun Mustér Turissem',
            'timestamp': 1444709160,
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
            'title': 'Le 19h30',
            'description': '',
            'upload_date': '20141201',
            'timestamp': 1417458600,
            'thumbnail': r're:^https?://.*\.image',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'https://www.srf.ch/play/tv/popupvideoplayer?id=c4dba0ca-e75b-43b2-a34f-f708a4932e01',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        bu = mobj.group('bu')
        media_type = mobj.group('type') or mobj.group('type_2')
        media_id = mobj.group('id')
        # other info can be extracted from url + '&layout=json'
        return self.url_result('srgssr:%s:%s:%s' % (bu[:3], media_type, media_id), 'SRGSSR')

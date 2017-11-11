# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    qualities,
)


class SRGSSRIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        https?://tp\.srgssr\.ch/p(?:/[^/]+)+\?urn=urn|
                        srgssr
                    ):
                    (?P<bu>
                        srf|rts|rsi|rtr|swi
                    ):(?:[^:]+:)?
                    (?P<type>
                        video|audio
                    ):
                    (?P<id>
                        [0-9a-f\-]{36}|\d+
                    )
                    '''
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
            'http://tp.srgssr.ch/akahd/token?acl=/%s/%s/*' % (sp[1], sp[2]),
            video_id, 'Downloading %s token' % format_id, fatal=False) or {}
        auth_params = token.get('token', {}).get('authparams')
        if auth_params:
            url += ('?' if '?' not in url else '&') + auth_params
        return url

    def _get_media_data(self, bu, media_type, media_id):
        query = {'onlyChapters': True} if media_type == 'video' else {}
        full_media_data = self._download_json(
            'https://il.srgssr.ch/integrationlayer/2.0/%s/mediaComposition/%s/%s.json'
            % (bu, media_type, media_id),
            media_id, query=query)['chapterList']
        try:
            media_data = next(
                x for x in full_media_data if x['id'] == media_id)
        except StopIteration:
            raise ExtractorError('No media information found')

        if media_data.get('blockReason') and media_data['blockReason'] in self._ERRORS:
            message = self._ERRORS[media_data['blockReason']]
            if media_data['blockReason'] == 'GEOBLOCK':
                self.raise_geo_restricted(
                    msg=message, countries=self._GEO_COUNTRIES)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, message), expected=True)

        return media_data

    def _get_subtitles(self, media_data, bu, media_type):
        subtitles = {}
        if media_type == 'audio':
            return subtitles

        subtitle_data = media_data.get('subtitleList', [])
        default_language_codes = {
            'srf': 'de',
            'rts': 'fr',
            'rsi': 'it',
            'rtr': 'rm',
            'swi': 'en',
        }
        known_formats = ('TTML', 'VTT')
        for sub in subtitle_data:
            form = sub['format']
            if form not in known_formats:
                continue
            lang = sub.get('locale') or default_language_codes[bu]
            subtitles.setdefault(lang, []).append({
                'ext': form.lower(),
                'url': sub['url']
            })
        # Prefer VTT subtitles over TTML:
        priorities = {
            'ttml': 1,
            'vtt': 2,
        }
        for lang in subtitles:
            subtitles[lang].sort(key=lambda x: priorities[x['ext']])

        return subtitles

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        media_data = self._get_media_data(bu, media_type, media_id)
        title = media_data['title']
        description = media_data.get('description')
        thumbnail = media_data.get('imageUrl')
        created_date = media_data.get('date')
        timestamp = parse_iso8601(created_date)
        duration = float_or_none(media_data['duration'], scale=1000)

        subtitles = self.extract_subtitles(media_data, bu, media_type)

        formats = []
        preference = qualities(['LQ', 'MQ', 'SD', 'HQ', 'HD'])
        for source in media_data.get('resourceList', []):
            protocol = source.get('protocol')
            quality = source.get('quality')
            encoding = source.get('encoding')
            mime_type = source.get('mimeType')
            format_url = source.get('url')
            format_id = '%s-%s-%s' % (protocol, encoding, quality)

            if protocol in ('HDS', 'HLS'):
                asset_url = self._get_tokenized_src(
                    format_url, media_id, format_id)
                if protocol == 'HDS':
                    formats.extend(self._extract_akamai_formats(
                        asset_url, media_id))
                else:
                    formats.extend(self._extract_m3u8_formats(
                        asset_url, media_id, 'mp4', 'm3u8_native',
                        m3u8_id=format_id, fatal=False
                    ))
            elif protocol in ('HTTP', 'HTTPS', 'RTMP'):
                formats.append({
                    'format_id': format_id,
                    'ext': mimetype2ext(mime_type) if mime_type else None,
                    'url': format_url,
                    'preference': preference(quality)
                })
            podcast_keys = ('podcastSdUrl', 'podcastHdUrl')
            podcast_qualities = ('SD', 'HD')

        # This is needed because for audio medias the podcast url is usually
        # always included, even if is only an audio segment and not the
        # whole episode.
        if int_or_none(media_data['position']) == 0:
            for key, quality in zip(podcast_keys, podcast_qualities):
                if media_data.get(key):
                    formats.append({
                        'format_id': 'PODCAST-%s' % quality,
                        'url': media_data[key],
                        'preference': preference(quality),
                    })
        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'subtitles': subtitles,
            'formats': formats,
        }


class SRGSSRPlayIE(InfoExtractor):
    IE_DESC = 'srf.ch, rts.ch, rsi.ch, rtr.ch and swissinfo.ch play sites'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                www|play
                            )\.
                        )?
                        (?P<bu>
                            srf|rts|rsi|rtr|swissinfo
                        )\.ch/play/
                        (?:
                            tv|radio
                        )/[^/]+/
                        (?P<type>
                            video|audio
                        )/[^?]+\?id=
                        (?P<id>
                            [0-9a-f\-]{36}|\d+
                        )
                    '''

    _TESTS = [{
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '9764693a295be9a24ce231440b200ba4',
        'info_dict': {
            'id': '28e1a57d-5b76-4399-8ab3-9097f071e6c5',
            'ext': 'mp4',
            'title': 'Snowden beantragt Asyl in Russland',
            'description': None,
            'duration': 113.827,
            'upload_date': '20130701',
            'timestamp': 1372708215,
            'thumbnail': r're:^https?://.*1383719781\.png$',
        },
    }, {
        'url': 'http://www.rtr.ch/play/radio/actualitad/audio/saira-tujetsch-tuttina-cuntinuar-cun-sedrun-muster-turissem?id=63cb0778-27f8-49af-9284-8c7a8c6d15fc',
        'info_dict': {
            'id': '63cb0778-27f8-49af-9284-8c7a8c6d15fc',
            'ext': 'mp3',
            'upload_date': '20151013',
            'title': 'Saira: Tujetsch - tuttina cuntinuar cun Sedrun Mustér Turissem',
            'duration': 336.839,
            'timestamp': 1444709160,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        'url': 'http://play.swissinfo.ch/play/tv/business/video/why-people-were-against-tax-reforms?id=42960270',
        'info_dict': {
            'id': '42960270',
            'ext': 'mp4',
            'title': 'Why people were against tax reforms',
            'description': 'md5:8c5c1b6a2a37c17670cf87f608ff4755',
            'duration': 94.0,
            'upload_date': '20170215',
            'timestamp': 1487173560,
            'thumbnail': 'https://www.swissinfo.ch/srgscalableimage/42961964',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        return self.url_result('srgssr:%s:%s:%s' % (bu[:3], media_type, media_id), 'SRGSSR')

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    ExtractorError,
    float_or_none,
    mimetype2ext,
    parse_iso8601,
    str_or_none,
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

    def _get_tokenized_src(self, url, video_id, format_id, segment_data):
        sp = compat_urllib_parse_urlparse(url).path.split('/')
        token = self._download_json(
            'http://tp.srgssr.ch/akahd/token?acl=/%s/%s/*' % (sp[1], sp[2]),
            video_id, 'Downloading %s token' % format_id, fatal=False) or {}
        auth_params = token.get('token', {}).get('authparams')
        if segment_data:
            timestep_string = self._get_timestep_token(segment_data)
            url += ('?' if '?' not in url else '&') + timestep_string
        if auth_params:
            url += ('?' if '?' not in url else '&') + auth_params
        return url

    def _get_timestep_token(self, segment_data):
        start = str_or_none(float_or_none(segment_data['markIn'], scale=1000))
        end = str_or_none(float_or_none(segment_data['markOut'], scale=1000))
        return 'start=%s&end=%s' % (start, end)

    def _extract_list_item(self, outer_data, key, item_id):
        data_list = outer_data.get(key, [])
        items = []
        if data_list:
            items.extend([item for item in data_list if item.get('id') == item_id])
        if not items:
            raise ExtractorError('%s said: Cannot extract %s' % (self.IE_NAME, key))

        item = items[0]
        block_reason = str_or_none(item.get('blockReason'))
        if block_reason and block_reason in self._ERRORS:
            message = self._ERRORS[block_reason]
            if block_reason == 'GEOBLOCK':
                self.raise_geo_restricted(
                    msg=message, countries=self._GEO_COUNTRIES)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, message), expected=True)
        elif block_reason:
            raise ExtractorError(
                '%s said: This media is not available. Reason %s' % (self.IE_NAME, block_reason))
        return item

    def _get_ids_and_data(self, bu, media_type, url_id):
        media_data = self._download_json(
            'https://il.srgssr.ch/integrationlayer/2.0/%s/mediaComposition/%s/%s.json' % (bu, media_type, url_id), url_id)
        urn_regex = r'urn:%s:%s:([0-9a-f\-]{36}|\d+)' % (bu, media_type)
        chapter_id = self._search_regex(
            urn_regex, media_data['chapterUrn'], 'chapter id')
        segment_urn = str_or_none(media_data.get('segmentUrn'))
        segment_id = self._search_regex(
            urn_regex,
            media_data['segmentUrn'],
            'segment id') if segment_urn else None
        return chapter_id, segment_id, media_data

    def _get_subtitles(self, bu, media_type, chapter_data, segment_data):
        subtitles = {}
        if media_type == 'audio':
            return subtitles

        subtitle_data = segment_data.get(
            'subtitleList', []) if segment_data else chapter_data.get(
            'subtitleList', [])

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

    def _get_thumbnail(self, chapter_data, segment_data):
        if segment_data:
            return segment_data.get('imageUrl')
        else:
            return chapter_data.get('imageUrl')

    def _real_extract(self, url):
        bu, media_type, url_id = re.match(self._VALID_URL, url).groups()

        chapter_id, segment_id, media_data = self._get_ids_and_data(
            bu, media_type, url_id)
        media_id = segment_id or chapter_id
        episode_data = media_data.get('episode', {})
        chapter_data = self._extract_list_item(
            media_data, 'chapterList', chapter_id)
        segment_data = self._extract_list_item(
            chapter_data, 'segmentList', segment_id) if segment_id else None

        is_whole_episode = True if chapter_data['position'] == 0 and not segment_id else False
        if media_type == 'video':
            title = chapter_data['title'] if is_whole_episode else segment_data['title']
            description = chapter_data.get(
                'description') if is_whole_episode else segment_data.get('description')
        else:
            # Audio media title and description set in chapter_data only refer to
            # the content of the first chapter, so we take these informations from
            # episode_data in case of a multi-chapter audio media.
            title = episode_data['title'] if is_whole_episode else chapter_data['title']
            description = episode_data.get(
                'description') if is_whole_episode else chapter_data.get('description')
        duration = float_or_none(
            segment_data['duration'], scale=1000) if segment_id else float_or_none(
            chapter_data['duration'], scale=1000)
        created_date = segment_data.get(
            'date') if segment_id else chapter_data.get('date')
        timestamp = parse_iso8601(created_date)
        thumbnail = self._get_thumbnail(chapter_data, segment_data)
        subtitles = self._get_subtitles(
            bu, media_type, chapter_data, segment_data)

        preference = qualities(['LQ', 'MQ', 'SD', 'HQ', 'HD'])
        formats = []
        for source in chapter_data.get('resourceList', []):
            protocol = str_or_none(source['protocol'])
            quality = str_or_none(source['quality'])
            encoding = str_or_none(source['encoding'])
            mime_type = str_or_none(source.get('mimeType'))
            format_url = source.get('url')
            format_id = '%s-%s-%s' % (protocol, encoding, quality)

            if protocol in ('HDS', 'HLS'):
                format_url = self._get_tokenized_src(
                    format_url, media_id, format_id, segment_data)
                if protocol == 'HDS':
                    formats.extend(self._extract_f4m_formats(
                        format_url + ('?' if '?' not in format_url else '&') + 'hdcore=3.4.0',
                        media_id, f4m_id=format_id, fatal=False))
                else:
                    formats.extend(self._extract_m3u8_formats(
                        format_url, media_id, 'mp4', 'm3u8_native',
                        m3u8_id=format_id, fatal=False))
            elif not segment_id and protocol in ('HTTP', 'HTTPS', 'RTMP'):
                formats.append({
                    'format_id': format_id,
                    'ext': mimetype2ext(mime_type) if mime_type else None,
                    'url': format_url,
                    'preference': preference(quality)
                })

        podcast_keys = ('podcastSdUrl', 'podcastHdUrl')
        podcast_qualities = ('SD', 'HD')
        if is_whole_episode:
            for key, quality in zip(podcast_keys, podcast_qualities):
                if chapter_data.get(key):
                    formats.append({
                        'format_id': 'PODCAST-HTTP-%s' % quality,
                        'url': chapter_data[key],
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
        # No save button, no description, only segment of a episode
        'url': 'http://www.srf.ch/play/tv/10vor10/video/snowden-beantragt-asyl-in-russland?id=28e1a57d-5b76-4399-8ab3-9097f071e6c5',
        'md5': '37040a6e7caa7bd25e9aad2f2f05e449',
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
        # With Save button, whole episode, german TTML and VTT subtitles (default language)
        'url': 'http://www.srf.ch/play/tv/rundschau/video/schwander-rot-gruene-stadtpolitik-min-li-marti-tamilen-kirche?id=2da578e3-dbb4-4657-a539-f01089a67831',
        'md5': 'b32af364dc9821af183da8dc1433da56',
        'info_dict': {
            'id': '2da578e3-dbb4-4657-a539-f01089a67831',
            'ext': 'mp4',
            'title': 'Schwander, Rot-Grüne Stadtpolitik, Min Li Marti, Tamilen-Kirche',
            'description': 'Verbissener Kampf / Vertreibung der Büezer / Theke: Min Li Marti / Geldsegen für den Pastor',
            'duration': 2630.0,
            'upload_date': '20170208',
            'timestamp': 1486583589,
            'thumbnail': r're:^https?://.*1486587225\.png$',
            'subtitles': {
                'de': [{
                    'ext': 'ttml',
                    'url': 're:^https://.*\.ttml$',
                }, {
                    'ext': 'vtt',
                    'url': 're:^https://.*\.vtt$',
                }]
            },
        },
    }, {
        # Video with many subtitles in different languages (explicit language definitions)
        'url': 'http://play.swissinfo.ch/play/tv/business/video/why-people-were-against-tax-reforms?id=42960270',
        'info_dict': {
            'id': '42960270',
            'ext': 'mp4',
            'title': 'Why people were against tax reforms',
            'description': 'md5:8c5c1b6a2a37c17670cf87f608ff4755',
            'upload_date': '20170215',
            'timestamp': 1487173560,
            'thumbnail': 'https://www.swissinfo.ch/srgscalableimage/42961964',
            'subtitles': {
                'ar': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'de': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'en': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'es': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'fr': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'it': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'ru': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
                'zh': [{'ext': 'vtt', 'url': 're:^https://.*\.vtt$'}],
            },
        },
        'params': {
            'skip_download': True,
        },

    }, {
        # Audio media with RTMP stream
        'url': 'http://www.rtr.ch/play/radio/actualitad/audio/saira-tujetsch-tuttina-cuntinuar-cun-sedrun-muster-turissem?id=63cb0778-27f8-49af-9284-8c7a8c6d15fc',
        'info_dict': {
            'id': '63cb0778-27f8-49af-9284-8c7a8c6d15fc',
            'ext': 'mp3',
            'title': 'Saira: Tujetsch - tuttina cuntinuar cun Sedrun Mustér Turissem',
            'upload_date': '20151013',
            'timestamp': 1444709160,
            'thumbnail': r're:^https?://.*1453369436\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {

        # Audio, whole episode of a show (i.e. chapter position 0)
        'url': 'http://www.srf.ch/play/radio/echo-der-zeit/audio/annur-moschee---rachezug-gegen-informanten?id=576a1fca-3cbd-48d7-be2f-e6dfc62a39d2',
        'info_dict': {
            'id': '576a1fca-3cbd-48d7-be2f-e6dfc62a39d2',
            'ext': 'mp3',
            'title': 'Echo der Zeit vom 21.02.2017 18:00:00',
            'description': None,
            'duration': 2419.07,
            'upload_date': '20170221',
            'timestamp': 1487696400,
            'thumbnail': r're:https://.*448775\.170221_echo_annur-winterthur-624\.jpg',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # Audio story of the show in the previous test, but not the whole episode
        'url': 'http://www.srf.ch/play/radio/echo-der-zeit/audio/slowenisch-oesterreichischer-nachbarschaftsstreit?id=03f76721-90b8-4d7f-8c14-176e4c4c4308',
        'info_dict': {
            'id': '03f76721-90b8-4d7f-8c14-176e4c4c4308',
            'ext': 'mp3',
            'title': 'Slowenisch-österreichischer Nachbarschaftsstreit',
            'description': 'md5:4f3c5a60e12759afe578c901bbcaa574',
            'duration': 182.387,
            'upload_date': '20170221',
            'timestamp': 1487696400,
            'thumbnail': r're:^https://.*448788\.170221_echo_slowenien-miro-cerar-624\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        # other info can be extracted from url + '&layout=json'
        return self.url_result('srgssr:%s:%s:%s' % (bu[:3], media_type, media_id), 'SRGSSR')

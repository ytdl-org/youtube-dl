from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    fix_xml_ampersands,
    parse_duration,
    qualities,
    strip_jsonp,
    unified_strdate,
)


class NPOBaseIE(InfoExtractor):
    def _get_token(self, video_id):
        token_page = self._download_webpage(
            'http://ida.omroep.nl/npoplayer/i.js',
            video_id, note='Downloading token')
        token = self._search_regex(
            r'npoplayer\.token = "(.+?)"', token_page, 'token')
        # Decryption algorithm extracted from http://npoplayer.omroep.nl/csjs/npoplayer-min.js
        token_l = list(token)
        first = second = None
        for i in range(5, len(token_l) - 4):
            if token_l[i].isdigit():
                if first is None:
                    first = i
                elif second is None:
                    second = i
        if first is None or second is None:
            first = 12
            second = 13

        token_l[first], token_l[second] = token_l[second], token_l[first]

        return ''.join(token_l)


class NPOIE(NPOBaseIE):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl and ntr.nl'
    _VALID_URL = r'''(?x)
                    (?:
                        npo:|
                        https?://
                            (?:www\.)?
                            (?:
                                npo\.nl/(?!live|radio)(?:[^/]+/){2}|
                                ntr\.nl/(?:[^/]+/){2,}|
                                omroepwnl\.nl/video/fragment/[^/]+__
                            )
                        )
                        (?P<id>[^/?#]+)
                '''

    _TESTS = [
        {
            'url': 'http://www.npo.nl/nieuwsuur/22-06-2014/VPWON_1220719',
            'md5': '4b3f9c429157ec4775f2c9cb7b911016',
            'info_dict': {
                'id': 'VPWON_1220719',
                'ext': 'm4v',
                'title': 'Nieuwsuur',
                'description': 'Dagelijks tussen tien en elf: nieuws, sport en achtergronden.',
                'upload_date': '20140622',
            },
        },
        {
            'url': 'http://www.npo.nl/de-mega-mike-mega-thomas-show/27-02-2009/VARA_101191800',
            'md5': 'da50a5787dbfc1603c4ad80f31c5120b',
            'info_dict': {
                'id': 'VARA_101191800',
                'ext': 'm4v',
                'title': 'De Mega Mike & Mega Thomas show: The best of.',
                'description': 'md5:3b74c97fc9d6901d5a665aac0e5400f4',
                'upload_date': '20090227',
                'duration': 2400,
            },
        },
        {
            'url': 'http://www.npo.nl/tegenlicht/25-02-2013/VPWON_1169289',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'Tegenlicht: De toekomst komt uit Afrika',
                'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
                'upload_date': '20130225',
                'duration': 3000,
            },
        },
        {
            'url': 'http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706',
            'info_dict': {
                'id': 'WO_VPRO_043706',
                'ext': 'wmv',
                'title': 'De nieuwe mens - Deel 1',
                'description': 'md5:518ae51ba1293ffb80d8d8ce90b74e4b',
                'duration': 4680,
            },
            'params': {
                # mplayer mms download
                'skip_download': True,
            }
        },
        # non asf in streams
        {
            'url': 'http://www.npo.nl/hoe-gaat-europa-verder-na-parijs/10-01-2015/WO_NOS_762771',
            'md5': 'b3da13de374cbe2d5332a7e910bef97f',
            'info_dict': {
                'id': 'WO_NOS_762771',
                'ext': 'mp4',
                'title': 'Hoe gaat Europa verder na Parijs?',
            },
        },
        {
            'url': 'http://www.ntr.nl/Aap-Poot-Pies/27/detail/Aap-poot-pies/VPWON_1233944#content',
            'md5': '01c6a2841675995da1f0cf776f03a9c3',
            'info_dict': {
                'id': 'VPWON_1233944',
                'ext': 'm4v',
                'title': 'Aap, poot, pies',
                'description': 'md5:c9c8005d1869ae65b858e82c01a91fde',
                'upload_date': '20150508',
                'duration': 599,
            },
        },
        {
            'url': 'http://www.omroepwnl.nl/video/fragment/vandaag-de-dag-verkiezingen__POMS_WNL_853698',
            'md5': 'd30cd8417b8b9bca1fdff27428860d08',
            'info_dict': {
                'id': 'POW_00996502',
                'ext': 'm4v',
                'title': '''"Dit is wel een 'landslide'..."''',
                'description': 'md5:f8d66d537dfb641380226e31ca57b8e8',
                'upload_date': '20150508',
                'duration': 462,
            },
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._get_info(video_id)

    def _get_info(self, video_id):
        metadata = self._download_json(
            'http://e.omroep.nl/metadata/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=strip_jsonp,
        )

        # For some videos actual video id (prid) is different (e.g. for
        # http://www.omroepwnl.nl/video/fragment/vandaag-de-dag-verkiezingen__POMS_WNL_853698
        # video id is POMS_WNL_853698 but prid is POW_00996502)
        video_id = metadata.get('prid') or video_id

        # titel is too generic in some cases so utilize aflevering_titel as well
        # when available (e.g. http://tegenlicht.vpro.nl/afleveringen/2014-2015/access-to-africa.html)
        title = metadata['titel']
        sub_title = metadata.get('aflevering_titel')
        if sub_title and sub_title != title:
            title += ': %s' % sub_title

        token = self._get_token(video_id)

        formats = []

        pubopties = metadata.get('pubopties')
        if pubopties:
            quality = qualities(['adaptive', 'wmv_sb', 'h264_sb', 'wmv_bb', 'h264_bb', 'wvc1_std', 'h264_std'])
            for format_id in pubopties:
                format_info = self._download_json(
                    'http://ida.omroep.nl/odi/?prid=%s&puboptions=%s&adaptive=yes&token=%s'
                    % (video_id, format_id, token),
                    video_id, 'Downloading %s JSON' % format_id)
                if format_info.get('error_code', 0) or format_info.get('errorcode', 0):
                    continue
                streams = format_info.get('streams')
                if streams:
                    video_info = self._download_json(
                        streams[0] + '&type=json',
                        video_id, 'Downloading %s stream JSON' % format_id)
                else:
                    video_info = format_info
                video_url = video_info.get('url')
                if not video_url:
                    continue
                if format_id == 'adaptive':
                    formats.extend(self._extract_m3u8_formats(video_url, video_id))
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                        'quality': quality(format_id),
                    })

        streams = metadata.get('streams')
        if streams:
            for i, stream in enumerate(streams):
                stream_url = stream.get('url')
                if not stream_url:
                    continue
                if '.asf' not in stream_url:
                    formats.append({
                        'url': stream_url,
                        'quality': stream.get('kwaliteit'),
                    })
                    continue
                asx = self._download_xml(
                    stream_url, video_id,
                    'Downloading stream %d ASX playlist' % i,
                    transform_source=fix_xml_ampersands)
                ref = asx.find('./ENTRY/Ref')
                if ref is None:
                    continue
                video_url = ref.get('href')
                if not video_url:
                    continue
                formats.append({
                    'url': video_url,
                    'ext': stream.get('formaat', 'asf'),
                    'quality': stream.get('kwaliteit'),
                })

        self._sort_formats(formats)

        subtitles = {}
        if metadata.get('tt888') == 'ja':
            subtitles['nl'] = [{
                'ext': 'vtt',
                'url': 'http://e.omroep.nl/tt888/%s' % video_id,
            }]

        return {
            'id': video_id,
            'title': title,
            'description': metadata.get('info'),
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'upload_date': unified_strdate(metadata.get('gidsdatum')),
            'duration': parse_duration(metadata.get('tijdsduur')),
            'formats': formats,
            'subtitles': subtitles,
        }


class NPOLiveIE(NPOBaseIE):
    IE_NAME = 'npo.nl:live'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/live/(?P<id>.+)'

    _TEST = {
        'url': 'http://www.npo.nl/live/npo-1',
        'info_dict': {
            'id': 'LI_NEDERLAND1_136692',
            'display_id': 'npo-1',
            'ext': 'mp4',
            'title': 're:^Nederland 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Livestream',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        live_id = self._search_regex(
            r'data-prid="([^"]+)"', webpage, 'live id')

        metadata = self._download_json(
            'http://e.omroep.nl/metadata/%s' % live_id,
            display_id, transform_source=strip_jsonp)

        token = self._get_token(display_id)

        formats = []

        streams = metadata.get('streams')
        if streams:
            for stream in streams:
                stream_type = stream.get('type').lower()
                # smooth streaming is not supported
                if stream_type in ['ss', 'ms']:
                    continue
                stream_info = self._download_json(
                    'http://ida.omroep.nl/aapi/?stream=%s&token=%s&type=jsonp'
                    % (stream.get('url'), token),
                    display_id, 'Downloading %s JSON' % stream_type)
                if stream_info.get('error_code', 0) or stream_info.get('errorcode', 0):
                    continue
                stream_url = self._download_json(
                    stream_info['stream'], display_id,
                    'Downloading %s URL' % stream_type,
                    'Unable to download %s URL' % stream_type,
                    transform_source=strip_jsonp, fatal=False)
                if not stream_url:
                    continue
                if stream_type == 'hds':
                    f4m_formats = self._extract_f4m_formats(stream_url, display_id)
                    # f4m downloader downloads only piece of live stream
                    for f4m_format in f4m_formats:
                        f4m_format['preference'] = -1
                    formats.extend(f4m_formats)
                elif stream_type == 'hls':
                    formats.extend(self._extract_m3u8_formats(stream_url, display_id, 'mp4'))
                else:
                    formats.append({
                        'url': stream_url,
                        'preference': -10,
                    })

        self._sort_formats(formats)

        return {
            'id': live_id,
            'display_id': display_id,
            'title': self._live_title(metadata['titel']),
            'description': metadata['info'],
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'formats': formats,
            'is_live': True,
        }


class NPORadioIE(InfoExtractor):
    IE_NAME = 'npo.nl:radio'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/radio/(?P<id>[^/]+)/?$'

    _TEST = {
        'url': 'http://www.npo.nl/radio/radio-1',
        'info_dict': {
            'id': 'radio-1',
            'ext': 'mp3',
            'title': 're:^NPO Radio 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    @staticmethod
    def _html_get_attribute_regex(attribute):
        return r'{0}\s*=\s*\'([^\']+)\''.format(attribute)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            self._html_get_attribute_regex('data-channel'), webpage, 'title')

        stream = self._parse_json(
            self._html_search_regex(self._html_get_attribute_regex('data-streams'), webpage, 'data-streams'),
            video_id)

        codec = stream.get('codec')

        return {
            'id': video_id,
            'url': stream['url'],
            'title': self._live_title(title),
            'acodec': codec,
            'ext': codec,
            'is_live': True,
        }


class NPORadioFragmentIE(InfoExtractor):
    IE_NAME = 'npo.nl:radio:fragment'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/radio/[^/]+/fragment/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.npo.nl/radio/radio-5/fragment/174356',
        'md5': 'dd8cc470dad764d0fdc70a9a1e2d18c2',
        'info_dict': {
            'id': '174356',
            'ext': 'mp3',
            'title': 'Jubileumconcert Willeke Alberti',
        },
    }

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(url, audio_id)

        title = self._html_search_regex(
            r'href="/radio/[^/]+/fragment/%s" title="([^"]+)"' % audio_id,
            webpage, 'title')

        audio_url = self._search_regex(
            r"data-streams='([^']+)'", webpage, 'audio url')

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
        }


class VPROIE(NPOIE):
    IE_NAME = 'vpro'
    _VALID_URL = r'https?://(?:www\.)?(?:tegenlicht\.)?vpro\.nl/(?:[^/]+/){2,}(?P<id>[^/]+)\.html'

    _TESTS = [
        {
            'url': 'http://tegenlicht.vpro.nl/afleveringen/2012-2013/de-toekomst-komt-uit-afrika.html',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'De toekomst komt uit Afrika',
                'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
                'upload_date': '20130225',
            },
        },
        {
            'url': 'http://www.vpro.nl/programmas/2doc/2015/sergio-herman.html',
            'info_dict': {
                'id': 'sergio-herman',
                'title': 'Sergio Herman: Fucking perfect',
            },
            'playlist_count': 2,
        },
        {
            # playlist with youtube embed
            'url': 'http://www.vpro.nl/programmas/2doc/2015/education-education.html',
            'info_dict': {
                'id': 'education-education',
                'title': '2Doc',
            },
            'playlist_count': 2,
        }
    ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result('npo:%s' % video_id if not video_id.startswith('http') else video_id)
            for video_id in re.findall(r'data-media-id="([^"]+)"', webpage)
        ]

        playlist_title = self._search_regex(
            r'<title>\s*([^>]+?)\s*-\s*Teledoc\s*-\s*VPRO\s*</title>',
            webpage, 'playlist title', default=None) or self._og_search_title(webpage)

        return self.playlist_result(entries, playlist_id, playlist_title)


class WNLIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?omroepwnl\.nl/video/detail/(?P<id>[^/]+)__\d+'

    _TEST = {
        'url': 'http://www.omroepwnl.nl/video/detail/vandaag-de-dag-6-mei__060515',
        'info_dict': {
            'id': 'vandaag-de-dag-6-mei',
            'title': 'Vandaag de Dag 6 mei',
        },
        'playlist_count': 4,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result('npo:%s' % video_id, 'NPO')
            for video_id, part in re.findall(
                r'<a[^>]+href="([^"]+)"[^>]+class="js-mid"[^>]*>(Deel \d+)', webpage)
        ]

        playlist_title = self._html_search_regex(
            r'(?s)<h1[^>]+class="subject"[^>]*>(.+?)</h1>',
            webpage, 'playlist title')

        return self.playlist_result(entries, playlist_id, playlist_title)

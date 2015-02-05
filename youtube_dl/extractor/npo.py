from __future__ import unicode_literals

from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    fix_xml_ampersands,
    parse_duration,
    qualities,
    strip_jsonp,
    unified_strdate,
    url_basename,
)


class NPOBaseIE(SubtitlesInfoExtractor):
    def _get_token(self, video_id):
        token_page = self._download_webpage(
            'http://ida.omroep.nl/npoplayer/i.js',
            video_id, note='Downloading token')
        return self._search_regex(
            r'npoplayer\.token = "(.+?)"', token_page, 'token')


class NPOIE(NPOBaseIE):
    IE_NAME = 'npo.nl'
    _VALID_URL = r'https?://www\.npo\.nl/[^/]+/[^/]+/(?P<id>[^/?]+)'

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
                'title': 'De Mega Mike & Mega Thomas show',
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
                'title': 'Tegenlicht',
                'description': 'md5:d6476bceb17a8c103c76c3b708f05dd1',
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
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self._get_info(video_id)

    def _get_info(self, video_id):
        metadata = self._download_json(
            'http://e.omroep.nl/metadata/aflevering/%s' % video_id,
            video_id,
            # We have to remove the javascript callback
            transform_source=strip_jsonp,
        )

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
            subtitles['nl'] = 'http://e.omroep.nl/tt888/%s' % video_id

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        subtitles = self.extract_subtitles(video_id, subtitles)

        return {
            'id': video_id,
            'title': metadata['titel'],
            'description': metadata['info'],
            'thumbnail': metadata.get('images', [{'url': None}])[-1]['url'],
            'upload_date': unified_strdate(metadata.get('gidsdatum')),
            'duration': parse_duration(metadata.get('tijdsduur')),
            'formats': formats,
            'subtitles': subtitles,
        }


class NPOLiveIE(NPOBaseIE):
    IE_NAME = 'npo.nl:live'
    _VALID_URL = r'https?://www\.npo\.nl/live/(?P<id>.+)'

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
                if stream_type == 'ss':
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
                    transform_source=strip_jsonp)
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


class TegenlichtVproIE(NPOIE):
    IE_NAME = 'tegenlicht.vpro.nl'
    _VALID_URL = r'https?://tegenlicht\.vpro\.nl/afleveringen/.*?'

    _TESTS = [
        {
            'url': 'http://tegenlicht.vpro.nl/afleveringen/2012-2013/de-toekomst-komt-uit-afrika.html',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'Tegenlicht',
                'description': 'md5:d6476bceb17a8c103c76c3b708f05dd1',
                'upload_date': '20130225',
            },
        },
    ]

    def _real_extract(self, url):
        name = url_basename(url)
        webpage = self._download_webpage(url, name)
        urn = self._html_search_meta('mediaurn', webpage)
        info_page = self._download_json(
            'http://rs.vpro.nl/v2/api/media/%s.json' % urn, name)
        return self._get_info(info_page['mid'])

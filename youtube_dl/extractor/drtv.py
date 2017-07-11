# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    mimetype2ext,
    parse_iso8601,
    remove_end,
    update_url_query,
)


class DRTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/(?:tv/se|nyheder|radio/ondemand)/(?:[^/]+/)*(?P<id>[\da-z-]+)(?:[/#?]|$)'
    _GEO_BYPASS = False
    _GEO_COUNTRIES = ['DK']
    IE_NAME = 'drtv'
    _TESTS = [{
        'url': 'https://www.dr.dk/tv/se/boern/ultra/klassen-ultra/klassen-darlig-taber-10',
        'md5': '7ae17b4e18eb5d29212f424a7511c184',
        'info_dict': {
            'id': 'klassen-darlig-taber-10',
            'ext': 'mp4',
            'title': 'Klassen - Dårlig taber (10)',
            'description': 'md5:815fe1b7fa656ed80580f31e8b3c79aa',
            'timestamp': 1471991907,
            'upload_date': '20160823',
            'duration': 606.84,
        },
    }, {
        # embed
        'url': 'https://www.dr.dk/nyheder/indland/live-christianias-rydning-af-pusher-street-er-i-gang',
        'info_dict': {
            'id': 'christiania-pusher-street-ryddes-drdkrjpo',
            'ext': 'mp4',
            'title': 'LIVE Christianias rydning af Pusher Street er i gang',
            'description': 'md5:2a71898b15057e9b97334f61d04e6eb5',
            'timestamp': 1472800279,
            'upload_date': '20160902',
            'duration': 131.4,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # with SignLanguage formats
        'url': 'https://www.dr.dk/tv/se/historien-om-danmark/-/historien-om-danmark-stenalder',
        'info_dict': {
            'id': 'historien-om-danmark-stenalder',
            'ext': 'mp4',
            'title': 'Historien om Danmark: Stenalder (1)',
            'description': 'md5:8c66dcbc1669bbc6f873879880f37f2a',
            'timestamp': 1490401996,
            'upload_date': '20170325',
            'duration': 3502.04,
            'formats': 'mincount:20',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if '>Programmet er ikke længere tilgængeligt' in webpage:
            raise ExtractorError(
                'Video %s is not available' % video_id, expected=True)

        video_id = self._search_regex(
            (r'data-(?:material-identifier|episode-slug)="([^"]+)"',
                r'data-resource="[^>"]+mu/programcard/expanded/([^"]+)"'),
            webpage, 'video id')

        programcard = self._download_json(
            'http://www.dr.dk/mu/programcard/expanded/%s' % video_id,
            video_id, 'Downloading video JSON')
        data = programcard['Data'][0]

        title = remove_end(self._og_search_title(
            webpage, default=None), ' | TV | DR') or data['Title']
        description = self._og_search_description(
            webpage, default=None) or data.get('Description')

        timestamp = parse_iso8601(data.get('CreatedTime'))

        thumbnail = None
        duration = None

        restricted_to_denmark = False

        formats = []
        subtitles = {}

        for asset in data['Assets']:
            kind = asset.get('Kind')
            if kind == 'Image':
                thumbnail = asset.get('Uri')
            elif kind in ('VideoResource', 'AudioResource'):
                duration = float_or_none(asset.get('DurationInMilliseconds'), 1000)
                restricted_to_denmark = asset.get('RestrictedToDenmark')
                asset_target = asset.get('Target')
                for link in asset.get('Links', []):
                    uri = link.get('Uri')
                    if not uri:
                        continue
                    target = link.get('Target')
                    format_id = target or ''
                    preference = None
                    if asset_target in ('SpokenSubtitles', 'SignLanguage'):
                        preference = -1
                        format_id += '-%s' % asset_target
                    if target == 'HDS':
                        f4m_formats = self._extract_f4m_formats(
                            uri + '?hdcore=3.3.0&plugin=aasp-3.3.0.99.43',
                            video_id, preference, f4m_id=format_id, fatal=False)
                        if kind == 'AudioResource':
                            for f in f4m_formats:
                                f['vcodec'] = 'none'
                        formats.extend(f4m_formats)
                    elif target == 'HLS':
                        formats.extend(self._extract_m3u8_formats(
                            uri, video_id, 'mp4', entry_protocol='m3u8_native',
                            preference=preference, m3u8_id=format_id,
                            fatal=False))
                    else:
                        bitrate = link.get('Bitrate')
                        if bitrate:
                            format_id += '-%s' % bitrate
                        formats.append({
                            'url': uri,
                            'format_id': format_id,
                            'tbr': int_or_none(bitrate),
                            'ext': link.get('FileFormat'),
                            'vcodec': 'none' if kind == 'AudioResource' else None,
                        })
                subtitles_list = asset.get('SubtitlesList')
                if isinstance(subtitles_list, list):
                    LANGS = {
                        'Danish': 'da',
                    }
                    for subs in subtitles_list:
                        if not subs.get('Uri'):
                            continue
                        lang = subs.get('Language') or 'da'
                        subtitles.setdefault(LANGS.get(lang, lang), []).append({
                            'url': subs['Uri'],
                            'ext': mimetype2ext(subs.get('MimeType')) or 'vtt'
                        })

        if not formats and restricted_to_denmark:
            self.raise_geo_restricted(
                'Unfortunately, DR is not allowed to show this program outside Denmark.',
                countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }


class DRTVLiveIE(InfoExtractor):
    IE_NAME = 'drtv:live'
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/(?:tv|TV)/live/(?P<id>[\da-z-]+)'
    _GEO_COUNTRIES = ['DK']
    _TEST = {
        'url': 'https://www.dr.dk/tv/live/dr1',
        'info_dict': {
            'id': 'dr1',
            'ext': 'mp4',
            'title': 're:^DR1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        channel_data = self._download_json(
            'https://www.dr.dk/mu-online/api/1.0/channel/' + channel_id,
            channel_id)
        title = self._live_title(channel_data['Title'])

        formats = []
        for streaming_server in channel_data.get('StreamingServers', []):
            server = streaming_server.get('Server')
            if not server:
                continue
            link_type = streaming_server.get('LinkType')
            for quality in streaming_server.get('Qualities', []):
                for stream in quality.get('Streams', []):
                    stream_path = stream.get('Stream')
                    if not stream_path:
                        continue
                    stream_url = update_url_query(
                        '%s/%s' % (server, stream_path), {'b': ''})
                    if link_type == 'HLS':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, channel_id, 'mp4',
                            m3u8_id=link_type, fatal=False, live=True))
                    elif link_type == 'HDS':
                        formats.extend(self._extract_f4m_formats(update_url_query(
                            '%s/%s' % (server, stream_path), {'hdcore': '3.7.0'}),
                            channel_id, f4m_id=link_type, fatal=False))
        self._sort_formats(formats)

        return {
            'id': channel_id,
            'title': title,
            'thumbnail': channel_data.get('PrimaryImageUri'),
            'formats': formats,
            'is_live': True,
        }

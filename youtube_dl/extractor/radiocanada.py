# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    find_xpath_attr,
    determine_ext,
    int_or_none,
    unified_strdate,
    xpath_element,
    ExtractorError,
    determine_protocol,
    unsmuggle_url,
)


class RadioCanadaIE(InfoExtractor):
    IE_NAME = 'radiocanada'
    _VALID_URL = r'(?:radiocanada:|https?://ici\.radio-canada\.ca/widgets/mediaconsole/)(?P<app_code>[^:/]+)[:/](?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://ici.radio-canada.ca/widgets/mediaconsole/medianet/7184272',
            'info_dict': {
                'id': '7184272',
                'ext': 'mp4',
                'title': 'Le parcours du tireur capté sur vidéo',
                'description': 'Images des caméras de surveillance fournies par la GRC montrant le parcours du tireur d\'Ottawa',
                'upload_date': '20141023',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            }
        },
        {
            # empty Title
            'url': 'http://ici.radio-canada.ca/widgets/mediaconsole/medianet/7754998/',
            'info_dict': {
                'id': '7754998',
                'ext': 'mp4',
                'title': 'letelejournal22h',
                'description': 'INTEGRALE WEB 22H-TJ',
                'upload_date': '20170720',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            # with protectionType but not actually DRM protected
            'url': 'radiocanada:toutv:140872',
            'info_dict': {
                'id': '140872',
                'title': 'Épisode 1',
                'series': 'District 31',
            },
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        app_code, video_id = re.match(self._VALID_URL, url).groups()

        metadata = self._download_xml(
            'http://api.radio-canada.ca/metaMedia/v1/index.ashx',
            video_id, note='Downloading metadata XML', query={
                'appCode': app_code,
                'idMedia': video_id,
            })

        def get_meta(name):
            el = find_xpath_attr(metadata, './/Meta', 'name', name)
            return el.text if el is not None else None

        # protectionType does not necessarily mean the video is DRM protected (see
        # https://github.com/rg3/youtube-dl/pull/18609).
        if get_meta('protectionType'):
            self.report_warning('This video is probably DRM protected.')

        device_types = ['ipad']
        if not smuggled_data:
            device_types.append('flash')
            device_types.append('android')

        formats = []
        error = None
        # TODO: extract f4m formats
        # f4m formats can be extracted using flashhd device_type but they produce unplayable file
        for device_type in device_types:
            validation_url = 'http://api.radio-canada.ca/validationMedia/v1/Validation.ashx'
            query = {
                'appCode': app_code,
                'idMedia': video_id,
                'connectionType': 'broadband',
                'multibitrate': 'true',
                'deviceType': device_type,
            }
            if smuggled_data:
                validation_url = 'https://services.radio-canada.ca/media/validation/v2/'
                query.update(smuggled_data)
            else:
                query.update({
                    # paysJ391wsHjbOJwvCs26toz and bypasslock are used to bypass geo-restriction
                    'paysJ391wsHjbOJwvCs26toz': 'CA',
                    'bypasslock': 'NZt5K62gRqfc',
                })
            v_data = self._download_xml(validation_url, video_id, note='Downloading %s XML' % device_type, query=query, fatal=False)
            v_url = xpath_text(v_data, 'url')
            if not v_url:
                continue
            if v_url == 'null':
                error = xpath_text(v_data, 'message')
                continue
            ext = determine_ext(v_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    v_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    v_url, video_id, f4m_id='hds', fatal=False))
            else:
                ext = determine_ext(v_url)
                bitrates = xpath_element(v_data, 'bitrates')
                for url_e in bitrates.findall('url'):
                    tbr = int_or_none(url_e.get('bitrate'))
                    if not tbr:
                        continue
                    f_url = re.sub(r'\d+\.%s' % ext, '%d.%s' % (tbr, ext), v_url)
                    protocol = determine_protocol({'url': f_url})
                    f = {
                        'format_id': '%s-%d' % (protocol, tbr),
                        'url': f_url,
                        'ext': 'flv' if protocol == 'rtmp' else ext,
                        'protocol': protocol,
                        'width': int_or_none(url_e.get('width')),
                        'height': int_or_none(url_e.get('height')),
                        'tbr': tbr,
                    }
                    mobj = re.match(r'(?P<url>rtmp://[^/]+/[^/]+)/(?P<playpath>[^?]+)(?P<auth>\?.+)', f_url)
                    if mobj:
                        f.update({
                            'url': mobj.group('url') + mobj.group('auth'),
                            'play_path': mobj.group('playpath'),
                        })
                    formats.append(f)
                    if protocol == 'rtsp':
                        base_url = self._search_regex(
                            r'rtsp://([^?]+)', f_url, 'base url', default=None)
                        if base_url:
                            base_url = 'http://' + base_url
                            formats.extend(self._extract_m3u8_formats(
                                base_url + '/playlist.m3u8', video_id, 'mp4',
                                'm3u8_native', m3u8_id='hls', fatal=False))
                            formats.extend(self._extract_f4m_formats(
                                base_url + '/manifest.f4m', video_id,
                                f4m_id='hds', fatal=False))
        if not formats and error:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)
        self._sort_formats(formats)

        subtitles = {}
        closed_caption_url = get_meta('closedCaption') or get_meta('closedCaptionHTML5')
        if closed_caption_url:
            subtitles['fr'] = [{
                'url': closed_caption_url,
                'ext': determine_ext(closed_caption_url, 'vtt'),
            }]

        return {
            'id': video_id,
            'title': get_meta('Title') or get_meta('AV-nomEmission'),
            'description': get_meta('Description') or get_meta('ShortDescription'),
            'thumbnail': get_meta('imageHR') or get_meta('imageMR') or get_meta('imageBR'),
            'duration': int_or_none(get_meta('length')),
            'series': get_meta('Emission'),
            'season_number': int_or_none('SrcSaison'),
            'episode_number': int_or_none('SrcEpisode'),
            'upload_date': unified_strdate(get_meta('Date')),
            'subtitles': subtitles,
            'formats': formats,
        }


class RadioCanadaAudioVideoIE(InfoExtractor):
    'radiocanada:audiovideo'
    _VALID_URL = r'https?://ici\.radio-canada\.ca/audio-video/media-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://ici.radio-canada.ca/audio-video/media-7527184/barack-obama-au-vietnam',
        'info_dict': {
            'id': '7527184',
            'ext': 'mp4',
            'title': 'Barack Obama au Vietnam',
            'description': 'Les États-Unis lèvent l\'embargo sur la vente d\'armes qui datait de la guerre du Vietnam',
            'upload_date': '20160523',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        return self.url_result('radiocanada:medianet:%s' % self._match_id(url))

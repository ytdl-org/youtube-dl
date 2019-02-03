# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    unified_strdate,
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
    _GEO_COUNTRIES = ['CA']

    def _call_api(self, path, video_id, app_code, query):
        query.update({
            'appCode': app_code,
            'idMedia': video_id,
            'output': 'json',
        })
        return self._download_json(
            'https://services.radio-canada.ca/media/' + path, video_id, headers={
                'Authorization': 'Client-Key 773aea60-0e80-41bb-9c7f-e6d7c3ad17fb'
            }, query=query)

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        app_code, video_id = re.match(self._VALID_URL, url).groups()

        metas = self._call_api('meta/v1/index.ashx', video_id, app_code, {})['Metas']

        def get_meta(name):
            for meta in metas:
                if meta.get('name') == name:
                    text = meta.get('text')
                    if text:
                        return text

        # protectionType does not necessarily mean the video is DRM protected (see
        # https://github.com/rg3/youtube-dl/pull/18609).
        if get_meta('protectionType'):
            self.report_warning('This video is probably DRM protected.')

        query = {
            'connectionType': 'hd',
            'deviceType': 'ipad',
            'multibitrate': 'true',
        }
        if smuggled_data:
            query.update(smuggled_data)
        v_data = self._call_api('validation/v2/', video_id, app_code, query)
        v_url = v_data.get('url')
        if not v_url:
            error = v_data['message']
            if error == "Le contenu sélectionné n'est pas disponible dans votre pays":
                raise self.raise_geo_restricted(error, self._GEO_COUNTRIES)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)
        formats = self._extract_m3u8_formats(v_url, video_id, 'mp4')
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
    _VALID_URL = r'https?://ici\.radio-canada\.ca/([^/]+/)*media-(?P<id>[0-9]+)'
    _TESTS = [{
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
    }, {
        'url': 'https://ici.radio-canada.ca/info/videos/media-7527184/barack-obama-au-vietnam',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        return self.url_result('radiocanada:medianet:%s' % self._match_id(url))

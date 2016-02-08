# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
)


class DRTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/tv/se/(?:[^/]+/)*(?P<id>[\da-z-]+)(?:[/#?]|$)'

    _TEST = {
        'url': 'https://www.dr.dk/tv/se/boern/ultra/panisk-paske/panisk-paske-5',
        'md5': 'dc515a9ab50577fa14cc4e4b0265168f',
        'info_dict': {
            'id': 'panisk-paske-5',
            'ext': 'mp4',
            'title': 'Panisk Påske (5)',
            'description': 'md5:ca14173c5ab24cd26b0fcc074dff391c',
            'timestamp': 1426984612,
            'upload_date': '20150322',
            'duration': 1455,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if '>Programmet er ikke længere tilgængeligt' in webpage:
            raise ExtractorError(
                'Video %s is not available' % video_id, expected=True)

        video_id = self._search_regex(
            r'data-(?:material-identifier|episode-slug)="([^"]+)"',
            webpage, 'video id')

        programcard = self._download_json(
            'http://www.dr.dk/mu/programcard/expanded/%s' % video_id,
            video_id, 'Downloading video JSON')
        data = programcard['Data'][0]

        title = data['Title']
        description = data['Description']
        timestamp = parse_iso8601(data['CreatedTime'])

        thumbnail = None
        duration = None

        restricted_to_denmark = False

        formats = []
        subtitles = {}

        for asset in data['Assets']:
            if asset['Kind'] == 'Image':
                thumbnail = asset['Uri']
            elif asset['Kind'] == 'VideoResource':
                duration = asset['DurationInMilliseconds'] / 1000.0
                restricted_to_denmark = asset['RestrictedToDenmark']
                spoken_subtitles = asset['Target'] == 'SpokenSubtitles'
                for link in asset['Links']:
                    uri = link['Uri']
                    target = link['Target']
                    format_id = target
                    preference = None
                    if spoken_subtitles:
                        preference = -1
                        format_id += '-spoken-subtitles'
                    if target == 'HDS':
                        formats.extend(self._extract_f4m_formats(
                            uri + '?hdcore=3.3.0&plugin=aasp-3.3.0.99.43',
                            video_id, preference, f4m_id=format_id))
                    elif target == 'HLS':
                        formats.extend(self._extract_m3u8_formats(
                            uri, video_id, 'mp4', preference=preference,
                            m3u8_id=format_id))
                    else:
                        bitrate = link.get('Bitrate')
                        if bitrate:
                            format_id += '-%s' % bitrate
                        formats.append({
                            'url': uri,
                            'format_id': format_id,
                            'tbr': bitrate,
                            'ext': link.get('FileFormat'),
                        })
                subtitles_list = asset.get('SubtitlesList')
                if isinstance(subtitles_list, list):
                    LANGS = {
                        'Danish': 'da',
                    }
                    for subs in subtitles_list:
                        lang = subs['Language']
                        subtitles[LANGS.get(lang, lang)] = [{'url': subs['Uri'], 'ext': 'vtt'}]

        if not formats and restricted_to_denmark:
            raise ExtractorError(
                'Unfortunately, DR is not allowed to show this program outside Denmark.', expected=True)

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

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
)


class DRTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dr\.dk/(?:tv/se|nyheder)/(?:[^/]+/)*(?P<id>[\da-z-]+)(?:[/#?]|$)'

    _TESTS = [{
        'url': 'https://www.dr.dk/tv/se/boern/ultra/klassen-ultra/klassen-darlig-taber-10',
        'md5': '25e659cccc9a2ed956110a299fdf5983',
        'info_dict': {
            'id': 'klassen-darlig-taber-10',
            'ext': 'mp4',
            'title': 'Klassen - Dårlig taber (10)',
            'description': 'md5:815fe1b7fa656ed80580f31e8b3c79aa',
            'timestamp': 1471991907,
            'upload_date': '20160823',
            'duration': 606.84,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.dr.dk/nyheder/indland/live-christianias-rydning-af-pusher-street-er-i-gang',
        'md5': '2c37175c718155930f939ef59952474a',
        'info_dict': {
            'id': 'christiania-pusher-street-ryddes-drdkrjpo',
            'ext': 'mp4',
            'title': 'LIVE Christianias rydning af Pusher Street er i gang',
            'description': '- Det er det fedeste, der er sket i 20 år, fortæller christianit til DR Nyheder.',
            'timestamp': 1472800279,
            'upload_date': '20160902',
            'duration': 131.4,
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
            if asset.get('Kind') == 'Image':
                thumbnail = asset.get('Uri')
            elif asset.get('Kind') == 'VideoResource':
                duration = float_or_none(asset.get('DurationInMilliseconds'), 1000)
                restricted_to_denmark = asset.get('RestrictedToDenmark')
                spoken_subtitles = asset.get('Target') == 'SpokenSubtitles'
                for link in asset.get('Links', []):
                    uri = link.get('Uri')
                    if not uri:
                        continue
                    target = link.get('Target')
                    format_id = target or ''
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
                            uri, video_id, 'mp4', entry_protocol='m3u8_native',
                            preference=preference, m3u8_id=format_id))
                    else:
                        bitrate = link.get('Bitrate')
                        if bitrate:
                            format_id += '-%s' % bitrate
                        formats.append({
                            'url': uri,
                            'format_id': format_id,
                            'tbr': int_or_none(bitrate),
                            'ext': link.get('FileFormat'),
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
                expected=True)

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

from __future__ import unicode_literals

from .subtitles import SubtitlesInfoExtractor
from .common import ExtractorError
from ..utils import parse_iso8601


class DRTVIE(SubtitlesInfoExtractor):
    _VALID_URL = r'http://(?:www\.)?dr\.dk/tv/se/(?:[^/]+/)+(?P<id>[\da-z-]+)(?:[/#?]|$)'

    _TEST = {
        'url': 'http://www.dr.dk/tv/se/partiets-mand/partiets-mand-7-8',
        'md5': '4a7e1dd65cdb2643500a3f753c942f25',
        'info_dict': {
            'id': 'partiets-mand-7-8',
            'ext': 'mp4',
            'title': 'Partiets mand (7:8)',
            'description': 'md5:a684b90a8f9336cd4aab94b7647d7862',
            'timestamp': 1403047940,
            'upload_date': '20140617',
            'duration': 1299.040,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        programcard = self._download_json(
            'http://www.dr.dk/mu/programcard/expanded/%s' % video_id, video_id, 'Downloading video JSON')

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
                for link in asset['Links']:
                    target = link['Target']
                    uri = link['Uri']
                    formats.append({
                        'url': uri + '?hdcore=3.3.0&plugin=aasp-3.3.0.99.43' if target == 'HDS' else uri,
                        'format_id': target,
                        'ext': link['FileFormat'],
                        'preference': -1 if target == 'HDS' else -2,
                    })
                subtitles_list = asset.get('SubtitlesList')
                if isinstance(subtitles_list, list):
                    LANGS = {
                        'Danish': 'dk',
                    }
                    for subs in subtitles_list:
                        lang = subs['Language']
                        subtitles[LANGS.get(lang, lang)] = subs['Uri']

        if not formats and restricted_to_denmark:
            raise ExtractorError(
                'Unfortunately, DR is not allowed to show this program outside Denmark.', expected=True)

        self._sort_formats(formats)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
            'subtitles': self.extract_subtitles(video_id, subtitles),
        }

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class ArchiveOrgIE(InfoExtractor):
    IE_NAME = 'archive.org'
    IE_DESC = 'archive.org videos'
    _VALID_URL = r'https?://(?:www\.)?archive\.org/details/(?P<id>[^?/]+)(?:[?].*)?$'
    _TESTS = [{
        'url': 'http://archive.org/details/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'md5': '8af1d4cf447933ed3c7f4871162602db',
        'info_dict': {
            'id': 'XD300-23_68HighlightsAResearchCntAugHumanIntellect',
            'ext': 'ogv',
            'title': '1968 Demo - FJCC Conference Presentation Reel #1',
            'description': 'md5:1780b464abaca9991d8968c877bb53ed',
            'upload_date': '19681210',
            'uploader': 'SRI International'
        }
    }, {
        'url': 'https://archive.org/details/Cops1922',
        'md5': '18f2a19e6d89af8425671da1cf3d4e04',
        'info_dict': {
            'id': 'Cops1922',
            'ext': 'ogv',
            'title': 'Buster Keaton\'s "Cops" (1922)',
            'description': 'md5:70f72ee70882f713d4578725461ffcc3',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_url = url + ('&' if '?' in url else '?') + 'output=json'
        data = self._download_json(json_url, video_id)

        def get_optional(data_dict, field):
            return data_dict['metadata'].get(field, [None])[0]

        title = get_optional(data, 'title')
        description = get_optional(data, 'description')
        uploader = get_optional(data, 'creator')
        upload_date = unified_strdate(get_optional(data, 'date'))

        formats = [
            {
                'format': fdata['format'],
                'url': 'http://' + data['server'] + data['dir'] + fn,
                'file_size': int(fdata['size']),
            }
            for fn, fdata in data['files'].items()
            if 'Video' in fdata['format']]

        self._sort_formats(formats)

        return {
            '_type': 'video',
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
            'upload_date': upload_date,
            'thumbnail': data.get('misc', {}).get('image'),
        }

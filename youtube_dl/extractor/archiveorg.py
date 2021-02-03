from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    clean_html,
)


class ArchiveOrgIE(InfoExtractor):
    IE_NAME = 'archive.org'
    IE_DESC = 'archive.org videos'
    _VALID_URL = r'https?://(?:www\.)?archive\.org/(?:details|embed)/(?P<id>[^/?#]+)(?:[?].*)?$'
    _TESTS = [{
        'url': 'http://archive.org/details/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'md5': '8af1d4cf447933ed3c7f4871162602db',
        'info_dict': {
            'id': 'XD300-23_68HighlightsAResearchCntAugHumanIntellect',
            'ext': 'ogv',
            'title': '1968 Demo - FJCC Conference Presentation Reel #1',
            'description': 'md5:da45c349df039f1cc8075268eb1b5c25',
            'upload_date': '19681210',
            'uploader': 'SRI International'
        }
    }, {
        'url': 'https://archive.org/details/Cops1922',
        'md5': '9b865bfdb0ca6b955b93f4a446ddce82',
        'info_dict': {
            'id': 'Cops1922',
            'ext': 'ogv',
            'title': 'Buster Keaton\'s "Cops" (1922)',
            'description': 'md5:43a603fd6c5b4b90d12a96b921212b9c',
        }
    }, {
        'url': 'http://archive.org/embed/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://archive.org/embed/' + video_id, video_id)
        jwplayer_playlist_string = self._search_regex(
            r"(?s)Play\('[^']+'\s*,\s*(\[.+\])\s*,\s*{.*?}\)",
            webpage, 'jwplayer playlist', default=None)
        info = {}
        if jwplayer_playlist_string:
            jwplayer_playlist = self._parse_json(jwplayer_playlist_string, video_id)
            info = self._parse_jwplayer_data({'playlist': jwplayer_playlist}, video_id, base_url=url)
        else:
            info['id'] = video_id
            info.update(self._parse_html5_media_entries("https://archive.org", webpage, video_id)[0])

        def get_optional(metadata, field):
            return metadata.get(field, [None])[0]

        metadata = self._download_json(
            'http://archive.org/details/' + video_id, video_id, query={
                'output': 'json',
            })['metadata']
        info.update({
            'title': get_optional(metadata, 'title') or info.get('title'),
            'description': clean_html(get_optional(metadata, 'description')),
        })
        if info.get('_type') != 'playlist':
            info.update({
                'uploader': get_optional(metadata, 'creator'),
                'upload_date': unified_strdate(get_optional(metadata, 'date')),
            })
        return info

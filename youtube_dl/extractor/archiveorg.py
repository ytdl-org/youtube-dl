from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    extract_attributes,
    unified_strdate,
    unified_timestamp,
)


class ArchiveOrgIE(InfoExtractor):
    IE_NAME = 'archive.org'
    IE_DESC = 'archive.org videos'
    _VALID_URL = r'https?://(?:www\.)?archive\.org/(?:details|embed)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://archive.org/details/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'md5': '8af1d4cf447933ed3c7f4871162602db',
        'info_dict': {
            'id': 'XD300-23_68HighlightsAResearchCntAugHumanIntellect',
            'ext': 'ogg',
            'title': '1968 Demo - FJCC Conference Presentation Reel #1',
            'description': 'md5:da45c349df039f1cc8075268eb1b5c25',
            'creator': 'SRI International',
            'release_date': '19681210',
            'uploader': 'SRI International',
            'timestamp': 1268695290,
            'upload_date': '20100315',
        }
    }, {
        'url': 'https://archive.org/details/Cops1922',
        'md5': '0869000b4ce265e8ca62738b336b268a',
        'info_dict': {
            'id': 'Cops1922',
            'ext': 'mp4',
            'title': 'Buster Keaton\'s "Cops" (1922)',
            'description': 'md5:43a603fd6c5b4b90d12a96b921212b9c',
            'timestamp': 1387699629,
            'upload_date': '20131222',
        }
    }, {
        'url': 'http://archive.org/embed/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'only_matching': True,
    }, {
        'url': 'https://archive.org/details/MSNBCW_20131125_040000_To_Catch_a_Predator/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://archive.org/embed/' + video_id, video_id)

        playlist = None
        play8 = self._search_regex(
            r'(<[^>]+\bclass=["\']js-play8-playlist[^>]+>)', webpage,
            'playlist', default=None)
        if play8:
            attrs = extract_attributes(play8)
            playlist = attrs.get('value')
        if not playlist:
            # Old jwplayer fallback
            playlist = self._search_regex(
                r"(?s)Play\('[^']+'\s*,\s*(\[.+\])\s*,\s*{.*?}\)",
                webpage, 'jwplayer playlist', default='[]')
        jwplayer_playlist = self._parse_json(playlist, video_id, fatal=False)
        if jwplayer_playlist:
            info = self._parse_jwplayer_data(
                {'playlist': jwplayer_playlist}, video_id, base_url=url)
        else:
            # HTML5 media fallback
            info = self._parse_html5_media_entries(url, webpage, video_id)[0]
            info['id'] = video_id

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
            creator = get_optional(metadata, 'creator')
            info.update({
                'creator': creator,
                'release_date': unified_strdate(get_optional(metadata, 'date')),
                'uploader': get_optional(metadata, 'publisher') or creator,
                'timestamp': unified_timestamp(get_optional(metadata, 'publicdate')),
                'language': get_optional(metadata, 'language'),
            })
        return info

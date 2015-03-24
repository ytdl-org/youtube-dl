# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    int_or_none,
    qualities,
)


class OdnoklassnikiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:odnoklassniki|ok)\.ru/(?:video|web-api/video/moviePlayer)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://ok.ru/video/20079905452',
        'md5': '8e24ad2da6f387948e7a7d44eb8668fe',
        'info_dict': {
            'id': '20079905452',
            'ext': 'mp4',
            'title': 'Культура меняет нас (прекрасный ролик!))',
            'duration': 100,
            'upload_date': '20141207',
            'uploader_id': '330537914540',
            'uploader': 'Виталий Добровольский',
            'like_count': int,
            'age_limit': 0,
        },
    }, {
        'url': 'http://ok.ru/web-api/video/moviePlayer/20079905452',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        player = self._parse_json(
            self._search_regex(
                r"OKVideo\.start\(({.+?})\s*,\s*'VideoAutoplay_player'", webpage, 'player'),
            video_id)

        metadata = self._parse_json(player['flashvars']['metadata'], video_id)

        movie = metadata['movie']
        title = movie['title']
        thumbnail = movie.get('poster')
        duration = int_or_none(movie.get('duration'))

        author = metadata.get('author', {})
        uploader_id = author.get('id')
        uploader = author.get('name')

        upload_date = unified_strdate(self._html_search_meta(
            'ya:ovs:upload_date', webpage, 'upload date'))

        age_limit = None
        adult = self._html_search_meta(
            'ya:ovs:adult', webpage, 'age limit')
        if adult:
            age_limit = 18 if adult == 'true' else 0

        like_count = int_or_none(metadata.get('likeCount'))

        quality = qualities(('mobile', 'lowest', 'low', 'sd', 'hd'))

        formats = [{
            'url': f['url'],
            'ext': 'mp4',
            'format_id': f['name'],
            'quality': quality(f['name']),
        } for f in metadata['videos']]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'upload_date': upload_date,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'like_count': like_count,
            'age_limit': age_limit,
            'formats': formats,
        }

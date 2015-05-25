# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    unified_strdate,
    int_or_none,
    qualities,
    unescapeHTML,
)


class OdnoklassnikiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:odnoklassniki|ok)\.ru/(?:video|web-api/video/moviePlayer)/(?P<id>[\d-]+)'
    _TESTS = [{
        # metadata in JSON
        'url': 'http://ok.ru/video/20079905452',
        'md5': '8e24ad2da6f387948e7a7d44eb8668fe',
        'info_dict': {
            'id': '20079905452',
            'ext': 'mp4',
            'title': 'Культура меняет нас (прекрасный ролик!))',
            'duration': 100,
            'uploader_id': '330537914540',
            'uploader': 'Виталий Добровольский',
            'like_count': int,
        },
    }, {
        # metadataUrl
        'url': 'http://ok.ru/video/63567059965189-0',
        'md5': '9676cf86eff5391d35dea675d224e131',
        'info_dict': {
            'id': '63567059965189-0',
            'ext': 'mp4',
            'title': 'Девушка без комплексов ...',
            'duration': 191,
            'uploader_id': '534380003155',
            'uploader': 'Андрей Мещанинов',
            'like_count': int,
        },
    }, {
        'url': 'http://ok.ru/web-api/video/moviePlayer/20079905452',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://ok.ru/video/%s' % video_id, video_id)

        player = self._parse_json(
            unescapeHTML(self._search_regex(
                r'data-attributes="([^"]+)"', webpage, 'player')),
            video_id)

        flashvars = player['flashvars']

        metadata = flashvars.get('metadata')
        if metadata:
            metadata = self._parse_json(metadata, video_id)
        else:
            metadata = self._download_json(
                compat_urllib_parse.unquote(flashvars['metadataUrl']),
                video_id, 'Downloading metadata JSON')

        movie = metadata['movie']
        title = movie['title']
        thumbnail = movie.get('poster')
        duration = int_or_none(movie.get('duration'))

        author = metadata.get('author', {})
        uploader_id = author.get('id')
        uploader = author.get('name')

        upload_date = unified_strdate(self._html_search_meta(
            'ya:ovs:upload_date', webpage, 'upload date', default=None))

        age_limit = None
        adult = self._html_search_meta(
            'ya:ovs:adult', webpage, 'age limit', default=None)
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

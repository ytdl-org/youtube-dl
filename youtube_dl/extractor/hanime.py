# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import clean_html


class HanimeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.tv/videos/hentai/(?P<id>.+)(?:\?playlist_id=\w+)?'
    _TEST = {
        'url': 'https://hanime.tv/videos/hentai/kuroinu-1',
        'info_dict': {
            'id': '33964',
            'display_id': 'kuroinu-1',
            'title': 'Kuroinu 1',
            'description': 'md5:37d5bb20d4a0834bd147bc1bac588a0b',
            'thumbnail': r're:^https?://.*\.jpg$',
            'release_date': '20120127',
            'upload_date': '20140509',
            'creator': 'Magin Label',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': list,
            'censored': True,
            'ext': 'mp4',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_slug = self._match_id(url)

        webpage = self._download_webpage(url, video_slug)
        page_json = self._html_search_regex(r'window.__NUXT__=(.+?);<\/script>', webpage, 'Inline JSON')
        page_json = self._parse_json(page_json, video_slug).get('state').get('data').get('video').get('hentai_video')
        api_json = self._download_json(
            'https://members.hanime.tv/api/v3/videos_manifests/%s' % video_slug,
            video_slug,
            'API Call', headers={'X-Directive': 'api'}
        )
        api_json = api_json.get('videos_manifest').get('servers')[0].get('streams')

        title = page_json.get('name') or api_json.get[0].get('video_stream_group_id')
        tags = [t.get('text') for t in page_json.get('hentai_tags')]

        video_id = str(api_json[0].get('id'))
        playlist_url = api_json[0].get('url') or api_json[1].get('url')
        formats = self._extract_m3u8_formats(playlist_url, video_slug, 'mp4')
        return {
            'id': video_id,
            'display_id': video_slug,
            'title': title,
            'description': clean_html(page_json.get('description')).strip(),
            'thumbnails': [
                {'id': 'Cover', 'url': page_json.get('cover_url')},
                {'id': 'Poster', 'url': page_json.get('poster_url')}
            ],
            'release_date': page_json.get('released_at').replace('-', '')[:8],
            'upload_date': page_json.get('created_at').replace('-', '')[:8],
            'creator': page_json.get('brand'),
            'view_count': page_json.get('views'),
            'like_count': page_json.get('likes'),
            'dislike_count': page_json.get('dislikes'),
            'tags': tags,
            'censored': page_json.get('is_censored'),
            'formats': formats,
        }

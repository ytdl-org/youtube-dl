# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    urljoin,
)

# compat_range
try:
    if callable(xrange):
        range = xrange
except (NameError, TypeError):
    pass


class CPACIE(InfoExtractor):
    IE_NAME = 'cpac'
    _VALID_URL = r'https?://(?:www\.)?cpac\.ca/(?P<fr>l-)?episode\?id=(?P<id>[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})'
    _TEST = {
        # 'url': 'http://www.cpac.ca/en/programs/primetime-politics/episodes/65490909',
        'url': 'https://www.cpac.ca/episode?id=fc7edcae-4660-47e1-ba61-5b7f29a9db0f',
        'md5': 'e46ad699caafd7aa6024279f2614e8fa',
        'info_dict': {
            'id': 'fc7edcae-4660-47e1-ba61-5b7f29a9db0f',
            'ext': 'mp4',
            'upload_date': '20220215',
            'title': 'News Conference to Celebrate National Kindness Week – February 15, 2022',
            'description': 'md5:466a206abd21f3a6f776cdef290c23fb',
            'timestamp': 1644901200,
        },
        'params': {
            'format': 'bestvideo',
            'hls_prefer_native': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url_lang = 'fr' if '/l-episode?' in url else 'en'

        content = self._download_json(
            'https://www.cpac.ca/api/1/services/contentModel.json?url=/site/website/episode/index.xml&crafterSite=cpacca&id=' + video_id,
            video_id)
        video_url = try_get(content, lambda x: x['page']['details']['videoUrl'], compat_str)
        formats = []
        if video_url:
            content = content['page']
            title = str_or_none(content['details']['title_%s_t' % (url_lang, )])
            formats = self._extract_m3u8_formats(video_url, video_id, m3u8_id='hls', ext='mp4')
            for fmt in formats:
                # prefer language to match URL
                fmt_lang = fmt.get('language')
                if fmt_lang == url_lang:
                    fmt['language_preference'] = 10
                elif not fmt_lang:
                    fmt['language_preference'] = -1
                else:
                    fmt['language_preference'] = -10

        self._sort_formats(formats)

        category = str_or_none(content['details']['category_%s_t' % (url_lang, )])

        def is_live(v_type):
            return (v_type == 'live') if v_type is not None else None

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': str_or_none(content['details'].get('description_%s_t' % (url_lang, ))),
            'timestamp': unified_timestamp(content['details'].get('liveDateTime')),
            'category': [category] if category else None,
            'thumbnail': urljoin(url, str_or_none(content['details'].get('image_%s_s' % (url_lang, )))),
            'is_live': is_live(content['details'].get('type')),
        }


class CPACPlaylistIE(InfoExtractor):
    IE_NAME = 'cpac:playlist'
    _VALID_URL = r'(?i)https?://(?:www\.)?cpac\.ca/(?:program|search|(?P<fr>emission|rechercher))\?(?:[^&]+&)*?(?P<id>(?:id=\d+|programId=\d+|key=[^&]+))'

    _TESTS = [{
        'url': 'https://www.cpac.ca/program?id=6',
        'info_dict': {
            'id': 'id=6',
            'title': 'Headline Politics',
            'description': 'Watch CPAC’s signature long-form coverage of the day’s pressing political events as they unfold.',
        },
        'playlist_count': 10,
    }, {
        'url': 'https://www.cpac.ca/search?key=hudson&type=all&order=desc',
        'info_dict': {
            'id': 'key=hudson',
            'title': 'hudson',
        },
        'playlist_count': 22,
    }, {
        'url': 'https://www.cpac.ca/search?programId=50',
        'info_dict': {
            'id': 'programId=50',
            'title': '50',
        },
        'playlist_count': 9,
    }, {
        'url': 'https://www.cpac.ca/emission?id=6',
        'only_matching': True,
    }, {
        'url': 'https://www.cpac.ca/rechercher?key=hudson&type=all&order=desc',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url_lang = 'fr' if any(x in url for x in ('/emission?', '/rechercher?')) else 'en'
        pl_type, list_type = ('program', 'itemList') if any(x in url for x in ('/program?', '/emission?')) else ('search', 'searchResult')
        api_url = (
            'https://www.cpac.ca/api/1/services/contentModel.json?url=/site/website/%s/index.xml&crafterSite=cpacca&%s'
            % (pl_type, video_id, ))
        content = self._download_json(api_url, video_id)
        entries = []
        total_pages = int_or_none(try_get(content, lambda x: x['page'][list_type]['totalPages']), default=1)
        for page in range(1, total_pages + 1):
            if page > 1:
                api_url = update_url_query(api_url, {'page': '%d' % (page, ), })
                content = self._download_json(
                    api_url, video_id,
                    note='Downloading continuation - %d' % (page, ),
                    fatal=False)

            for item in try_get(content, lambda x: x['page'][list_type]['item'], list) or []:
                episode_url = urljoin(url, try_get(item, lambda x: x['url_%s_s' % (url_lang, )]))
                if episode_url:
                    entries.append(episode_url)

        return self.playlist_result(
            (self.url_result(entry) for entry in entries),
            playlist_id=video_id,
            playlist_title=try_get(content, lambda x: x['page']['program']['title_%s_t' % (url_lang, )]) or video_id.split('=')[-1],
            playlist_description=try_get(content, lambda x: x['page']['program']['description_%s_t' % (url_lang, )]),
        )

# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    int_or_none,
    mimetype2ext,
    remove_end,
    clean_html,
    get_element_by_class,
    get_elements_by_class,
    unified_strdate,
)


class IwaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|ecchi\.)?iwara\.tv/videos/(?P<id>[a-zA-Z0-9]+)'
    _TESTS = [{
        'url': 'http://iwara.tv/videos/amVwUl1EHpAD9RD',
        # md5 is unstable
        'info_dict': {
            'id': 'amVwUl1EHpAD9RD',
            'ext': 'mp4',
            'title': '【MMD R-18】ガールフレンド carry_me_off',
            'age_limit': 18,
            'upload_date': '20150828',
            'uploader': 'Reimu丨Action',
            'description': '禁止转载\n\n=acfun=\n=bilibili=\n=youtube=\n\n=stage=\n=motion=\n=camera=\n=dress=',
            'comment_count': int,
            'like_count': int,
            'view_count': int,
        },
    }, {
        'url': 'http://ecchi.iwara.tv/videos/Vb4yf2yZspkzkBO',
        'md5': '7e5f1f359cd51a027ba4a7b7710a50f0',
        'info_dict': {
            'id': '0B1LvuHnL-sRFNXB1WHNqbGw4SXc',
            'ext': 'mp4',
            'title': '[3D Hentai] Kyonyu × Genkai × Emaki Shinobi Girls.mp4',
            'age_limit': 18,
        },
        'add_ie': ['GoogleDrive'],
    }, {
        'url': 'http://www.iwara.tv/videos/nawkaumd6ilezzgq',
        # md5 is unstable
        'info_dict': {
            'id': '6liAP9s2Ojc',
            'ext': 'mp4',
            'age_limit': 18,
            'title': '[MMD] Do It Again Ver.2 [1080p 60FPS] (Motion,Camera,Wav+DL)',
            'description': 'md5:590c12c0df1443d833fbebe05da8c47a',
            'upload_date': '20160910',
            'uploader': 'aMMDsork',
            'uploader_id': 'UCVOFyOSCyFkXTYYHITtqB7A',
        },
        'add_ie': ['Youtube'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage, urlh = self._download_webpage_handle(url, video_id)

        hostname = compat_urllib_parse_urlparse(urlh.geturl()).hostname
        # ecchi is 'sexy' in Japanese
        age_limit = 18 if hostname.split('.')[0] == 'ecchi' else 0

        video_data = self._download_json('http://www.iwara.tv/api/video/%s' % video_id, video_id)

        if not video_data:
            iframe_url = self._html_search_regex(
                r'<iframe[^>]+src=([\'"])(?P<url>[^\'"]+)\1',
                webpage, 'iframe URL', group='url')
            return {
                '_type': 'url_transparent',
                'url': iframe_url,
                'age_limit': age_limit,
            }

        title = remove_end(self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title'), ' | Iwara')

        upload_date = unified_strdate(self._html_search_regex(
            r'(\d{4}-\d{2}-\d{2})', webpage, 'upload_date', fatal=False))

        uploader = get_element_by_class('username', webpage)

        description_class = get_element_by_class('field-type-text-with-summary', webpage)
        description = clean_html(description_class.replace('</p>', '<br /></p>') if description_class else None)

        comment_count_classes = get_elements_by_class('title', webpage)
        comment_count = None
        if comment_count_classes and len(comment_count_classes) >= 2:
            comment_count = int_or_none(''.join(digit for digit in comment_count_classes[1] if digit.isdigit()))

        node_views_class = clean_html(get_element_by_class('node-views', webpage))
        node_views = node_views_class.split() if node_views_class else None
        like_count = view_count = None
        if node_views and len(node_views) >= 2:
            like_count = int_or_none(node_views[0].replace(',', ''))
            view_count = int_or_none(node_views[1].replace(',', ''))

        formats = []
        for a_format in video_data:
            format_id = a_format.get('resolution')
            height = int_or_none(self._search_regex(
                r'(\d+)p', format_id, 'height', default=None))
            formats.append({
                'url': a_format['uri'],
                'format_id': format_id,
                'ext': mimetype2ext(a_format.get('mime')) or 'mp4',
                'height': height,
                'width': int_or_none(height / 9.0 * 16.0 if height else None),
                'quality': 1 if format_id == 'Source' else 0,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'age_limit': age_limit,
            'formats': formats,
            'upload_date': upload_date,
            'uploader': uploader,
            'description': description,
            'comment_count': comment_count,
            'like_count': like_count,
            'view_count': view_count,
        }

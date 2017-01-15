# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    remove_end,
    mimetype2ext,
)


class IwaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|ecchi\.)?iwara\.tv/videos/(?P<id>[a-zA-Z0-9]+)'
    _TESTS = [{
        'url': 'http://iwara.tv/videos/amVwUl1EHpAD9RD',
        'md5': 'c9c35657eff2fda5af7f78e69637d2d6',
        'info_dict': {
            'id': 'amVwUl1EHpAD9RD',
            'ext': 'mp4',
            'title': '【MMD R-18】ガールフレンド carry_me_off',
            'age_limit': 18,
        },
    }, {
        'url': 'http://www.iwara.tv/videos/64zbul0qujvjavm',
        'md5': '727d0f869035247781469aa7a06e2365',
        'info_dict': {
            'id': '64zbul0qujvjavm',
            'ext': 'mp4',
            'title': 'レアさん Dark Sea Adventure',
            'age_limit': 0,
        },
    }, {
        'url': 'http://ecchi.iwara.tv/videos/Vb4yf2yZspkzkBO',
        'md5': '7e5f1f359cd51a027ba4a7b7710a50f0',
        'info_dict': {
            'id': '0B1LvuHnL-sRFNXB1WHNqbGw4SXc',
            'ext': 'mp4',
            'title': '[3D Hentai] Kyonyu Ã\x97 Genkai Ã\x97 Emaki Shinobi Girls.mp4',
            'age_limit': 18,
        },
        'add_ie': ['GoogleDrive'],
    }, {
        'url': 'http://ecchi.iwara.tv/videos/nawkaumd6ilezzgq',
        'md5': '729a1e0a830469fe2c56d20aed06f852',
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

        title = remove_end(self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title'), ' | Iwara')

        entries = self._parse_html5_media_entries(url, webpage, video_id)

        if entries:
            info_dict = entries[0]
            info_dict.update({
                'id': video_id,
                'title': title,
                'age_limit': age_limit,
            })

            return info_dict

        iframe_url = self._html_search_regex(
            r'<iframe[^>]+src=([\'"])(?P<url>[^\'"]+)\1',
            webpage, 'iframe URL', group='url', default=None)

        if iframe_url:
            return {
                '_type': 'url_transparent',
                'url': iframe_url,
                'age_limit': age_limit,
            }

        api_url = 'http://%s/api/video/%s' % (hostname, video_id)

        raw_formats = self._download_json(
            api_url, video_id,
            note='Downloading formats')

        formats = []

        for raw_format in raw_formats:
            new_format = {
                'url': raw_format.get('uri'),
                'resolution': raw_format.get('resolution'),
                'format_id': raw_format.get('resolution'),
            }

            if raw_format.get('resolution') == '1080p':
                height = 1080
            elif raw_format.get('resolution') == '720p':
                height = 720
            elif raw_format.get('resolution') == '540p':
                height = 540
            elif raw_format.get('resolution') == '360p':
                height = 360
            else:
                height = None

            if height is not None:
                new_format['width'] = int(height / 9.0 * 16.0)
                new_format['height'] = height

            if raw_format.get('mime'):
                new_format['ext'] = mimetype2ext(raw_format.get('mime'))

            formats.append(new_format)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'age_limit': age_limit,
            'formats': formats,
        }

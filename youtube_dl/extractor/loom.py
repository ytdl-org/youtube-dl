from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urllib_request
)
from ..utils import (
    js_to_json,
    try_get,
    unified_timestamp,
    url_or_none
)


class LoomBaseInfoIE(InfoExtractor):
    _BASE_URL = 'https://www.loom.com/'

    def _extract_video_info_json(self, webpage, video_id):
        info = self._html_search_regex(
            r'window.loomSSRVideo = (.+?);',
            webpage,
            'info')
        return self._parse_json(info, 'json', js_to_json)

    def _get_url_by_id_type(self, video_id, type):
        request = compat_urllib_request.Request(
            self._BASE_URL + 'api/campaigns/sessions/' + video_id + '/' + type,
            {})
        (json, _) = self._download_json_handle(request, video_id)
        return (url_or_none(json.get('url')), json.get('part_credentials'))

    def _get_m3u8_formats(self, url, video_id, credentials):
        format_list = self._extract_m3u8_formats(url, video_id)
        for item in format_list:
            item['protocol'] = 'm3u8_native'
            item['url'] += '?' + credentials
            item['ext'] = 'mp4'
            item['format_id'] = 'hls-' + str(item.get('height', 0))
            item['extra_param_to_segment_url'] = credentials
        return format_list


class LoomIE(LoomBaseInfoIE):
    _VALID_URL = r'https?://(?:www\.)?loom\.com/share/(?P<id>[a-zA-Z0-9]+)'
    _TESTS = [
        {
            'url': 'https://www.loom.com/share/31b41727a5b24dacb6c1417a565b2ebf',
            'md5': '8b94361aabff2075141dc60bd6d35453',
            'info_dict': {
                'id': '31b41727a5b24dacb6c1417a565b2ebf',
                'ext': 'mp4',
                'title': 'How to resize your camera bubble',
                'uploader': 'Allie Hitchcock',
                'upload_date': '20201007',
                'timestamp': 1602089241
            }
        },
        {
            'url': 'https://www.loom.com/share/7e5168ec3b0744cab5e08a340cc7e086',
            'md5': '47dd14aa1d8054c249b68ca57ad9963f',
            'info_dict': {
                'id': '7e5168ec3b0744cab5e08a340cc7e086',
                'ext': 'mp4',
                'title': 'How to flip your camera ',
                'uploader': 'Matthew Flores',
                'upload_date': '20200423',
                'timestamp': 1587646164
            }
        },
        {
            'url': 'https://www.loom.com/share/6670e3eba3c84dc09ada8306c7138075',
            'md5': 'bfad8181ed49d6252b10dfdeb46c535e',
            'info_dict': {
                'id': '6670e3eba3c84dc09ada8306c7138075',
                'ext': 'mp4',
                'title': 'How to record your first video on Loom',
                'uploader': 'Allie Hitchcock',
                'upload_date': '20201118',
                'timestamp': 1605729404
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = self._extract_video_info_json(webpage, video_id)

        formats = []
        for type in ['transcoded-url', 'raw-url']:
            (url, part_credentials) = self._get_url_by_id_type(video_id, type)
            ext = self._search_regex(
                r'\.([a-zA-Z0-9]+)\?',
                url, 'ext', default=None)
            if(ext != 'm3u8'):
                formats.append({
                    'url': url,
                    'ext': ext,
                    'format_id': type,
                    'width': try_get(info, lambda x: x['video_properties']['width']),
                    'height': try_get(info, lambda x: x['video_properties']['height'])
                })
            else:
                credentials = compat_urllib_parse_urlencode(part_credentials)
                m3u8_formats = self._get_m3u8_formats(url, video_id, credentials)
                for i in range(len(m3u8_formats)):
                    formats.insert(
                        (-1, len(formats))[i == len(m3u8_formats) - 1],
                        m3u8_formats[i])

        return {
            'id': info.get('id'),
            'title': info.get('name'),
            'formats': formats,
            'thumbnails': [
                {
                    'id': key,
                    'url': url_or_none(self._BASE_URL + value)
                } for key, value in info.get('thumbnails').items()
            ],
            'description': info.get('description'),
            'uploader': info.get('owner_full_name'),
            'timestamp': unified_timestamp(info.get('createdAt'))
        }

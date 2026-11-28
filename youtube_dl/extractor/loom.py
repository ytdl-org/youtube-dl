from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor

from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
    compat_urllib_request
)
from ..utils import (
    int_or_none,
    js_to_json,
    try_get,
    unified_timestamp,
    url_or_none
)


class LoomBaseInfoIE(InfoExtractor):
    _BASE_URL = 'https://www.loom.com/'


class LoomIE(LoomBaseInfoIE):
    _VALID_URL = r'https?://(?:www\.)?loom\.com/share/(?!folder)(?P<id>[a-zA-Z0-9]+)'
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

        info_json = self._html_search_regex(
            r'window.loomSSRVideo = (.+?);',
            webpage,
            'info')
        info = self._parse_json(info_json, 'json', js_to_json)

        formats = []
        for type in ['transcoded-url', 'raw-url']:
            json_doc = self._download_json(
                self._BASE_URL + 'api/campaigns/sessions/' + video_id + '/' + type,
                video_id, data={})
            url = url_or_none(json_doc.get('url'))
            part_credentials = json_doc.get('part_credentials')

            ext = self._search_regex(
                r'\.([a-zA-Z0-9]+)\?',
                url, 'ext', default=None)
            if ext != 'm3u8':
                formats.append({
                    'url': url,
                    'ext': ext,
                    'format_id': type,
                    'width': int_or_none(try_get(info, lambda x: x['video_properties']['width'])),
                    'height': int_or_none(try_get(info, lambda x: x['video_properties']['height']))
                })
            else:
                credentials = compat_urllib_parse_urlencode(part_credentials)
                m3u8_formats = self._extract_m3u8_formats(url, video_id)
                for item in m3u8_formats:
                    item['protocol'] = 'm3u8_native'
                    item['url'] += '?' + credentials
                    item['ext'] = 'mp4'
                    item['format_id'] = 'hls-' + str(item.get('height', 0))
                    item['extra_param_to_segment_url'] = credentials
                for i in range(len(m3u8_formats)):
                    formats.insert(
                        (-1, len(formats))[i == len(m3u8_formats) - 1],
                        m3u8_formats[i])

        return {
            'id': info.get('id') or video_id,
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


class LoomFolderIE(LoomBaseInfoIE):
    _VALID_URL = r'https?://(?:www\.)?loom\.com/share/folder/(?P<id>.+)/?'
    _TESTS = [
        {
            'url': 'https://www.loom.com/share/folder/997db4db046f43e5912f10dc5f817b5c/List%20A-%20a%2C%20i%2C%20o',
            'info_dict': {
                'id': '9a8a87f6b6f546d9a400c8e7575ff7f2',
                'title': 'List A- a, i, o'
            },
            'playlist_mincount': 12
        },
        {
            'url': 'https://www.loom.com/share/folder/997db4db046f43e5912f10dc5f817b5c',
            'info_dict': {
                'id': '997db4db046f43e5912f10dc5f817b5c',
                'title': 'Blending Lessons '
            },
            'playlist_mincount': 16
        }
    ]

    def _get_real_folder_id(self, path):
        subfolders = re.match(
            r'^([a-zA-Z0-9]+)(?:\/(.+))*$',
            compat_urllib_parse_unquote(path))
        folder_names = subfolders.groups()[1:]
        parent_folder_id = subfolders.group(1)
        if(folder_names[0] is None):
            return path

        # Fetch folder id
        request = compat_urllib_request.Request(
            self._BASE_URL + 'v1/folders/by_name',
            json.dumps({
                'folder_names': folder_names,
                'parent_folder_id': parent_folder_id
            }).encode('utf-8'))
        json_doc = self._download_json(request, parent_folder_id)

        return try_get(json_doc, lambda x: x['current_folder']['id'])

    def _get_folder_info(self, folder_id):
        json_doc = self._download_json(url_or_none(self._BASE_URL + 'v1/folders/' + folder_id), folder_id)
        videos = []

        # Recursive call for subfolder
        for folder in json_doc.get('folders'):
            subfolder_info = self._get_folder_info(folder.get('id'))
            videos.extend(subfolder_info.get('entries'))
        videos.extend([val.get('id') for val in json_doc.get('videos')])

        return {
            'id': folder_id,
            'title': json_doc.get('name'),
            'description': json_doc.get('description'),
            'entries': videos
        }

    def _real_extract(self, url):
        folder_id = self._match_id(url)
        folder_id = self._get_real_folder_id(folder_id)
        folder_info = self._get_folder_info(folder_id)
        folder_info['_type'] = 'playlist'

        for i in range(len(folder_info['entries'])):
            video_id = folder_info['entries'][i]
            folder_info['entries'][i] = self.url_result(url_or_none(self._BASE_URL + 'share/' + video_id), 'Loom', video_id)

        return folder_info

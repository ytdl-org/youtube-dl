# coding: utf-8
from __future__ import unicode_literals

import hashlib
import time

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    sanitized_Request,
    str_or_none,
)


def _get_api_key(api_path):
    if api_path.endswith('?'):
        api_path = api_path[:-1]

    api_key = 'fb5f58a820353bd7095de526253c14fd'
    a = '{0:}{1:}{2:}'.format(api_key, api_path, int(round(time.time() / 24 / 3600)))
    return hashlib.md5(a.encode('ascii')).hexdigest()


class StreamCZBaseIE(InfoExtractor):
    _API_URL = 'http://www.stream.cz/API'

    def _get_api_request(self, api_path, api_key):
        req = sanitized_Request(self._API_URL + api_path)
        req.add_header('Api-Password', _get_api_key(api_path))
        return req


class StreamCZIE(StreamCZBaseIE):
    _VALID_URL = r'(?:https?://(?:www\.)?stream\.cz/(?!porady|pohadky).+/|streamcz:)(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://www.stream.cz/peklonataliri/765767-ecka-pro-deti',
        'md5': '934bb6a6d220d99c010783c9719960d5',
        'info_dict': {
            'id': '765767',
            'ext': 'mp4',
            'title': 'Peklo na talíři: Éčka pro děti',
            'description': 'Taška s grónskou pomazánkou a další pekelnosti ZDE',
            'thumbnail': 're:^http://im.stream.cz/episode/52961d7e19d423f8f06f0100',
            'duration': 256,
        },
    }, {
        'url': 'http://www.stream.cz/blanik/10002447-tri-roky-pro-mazanka',
        'md5': '849a88c1e1ca47d41403c2ba5e59e261',
        'info_dict': {
            'id': '10002447',
            'ext': 'mp4',
            'title': 'Kancelář Blaník: Tři roky pro Mazánka',
            'description': 'md5:3862a00ba7bf0b3e44806b544032c859',
            'thumbnail': 're:^http://im.stream.cz/episode/537f838c50c11f8d21320000',
            'duration': 368,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_path = '/episode/%s' % video_id

        req = self._get_api_request(api_path, _get_api_key(api_path))
        data = self._download_json(req, video_id)

        formats = []
        for quality, video in enumerate(data['video_qualities']):
            for f in video['formats']:
                typ = f['type'].partition('/')[2]
                qlabel = video.get('quality_label')
                formats.append({
                    'format_note': '%s-%s' % (qlabel, typ) if qlabel else typ,
                    'format_id': '%s-%s' % (typ, f['quality']),
                    'url': f['source'],
                    'height': int_or_none(f['quality'].rstrip('p')),
                    'quality': quality,
                })
        self._sort_formats(formats)

        image = data.get('image')
        if image:
            thumbnail = self._proto_relative_url(
                image.replace('{width}', '1240').replace('{height}', '697'),
                scheme='http:',
            )
        else:
            thumbnail = None

        stream = data.get('_embedded', {}).get('stream:show', {}).get('name')
        if stream:
            title = '%s: %s' % (stream, data['name'])
        else:
            title = data['name']

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': data.get('web_site_text'),
            'duration': int_or_none(data.get('duration')),
            'view_count': int_or_none(data.get('views')),
        }


class StreamCZPlaylistIE(StreamCZBaseIE):
    _VALID_URL = r'https?://(?:www\.)?stream\.cz/(:?porady|pohadky)/(?P<id>.+)'

    _TESTS = [{
        'url': 'https://www.stream.cz/pohadky/lego-staveni',
        'info_dict': {
            'id': 'lego-staveni',
            'title': 'LEGO stavění',
            'description': 'md5:af5a439c7d84de87d3d11f8bc554cb19'
        },
        'params': {
            'skip_download': True,
        },
        'playlist_mincount': 34,
    }, {
        'url': 'https://www.stream.cz/porady/menudomu/serie/bonusy',
        'info_dict': {
            'id': 'menudomu/serie/bonusy',
            'title': 'MENU domů',
            'description': 'md5:f28221c0ecdf2553f55a671fb2f61882'
        },
        'params': {
            'skip_download': True,
        },
        'playlist_mincount': 14,
    }]

    def _extract_ids_from_playlist(self, playlist_id):
        episode_ids = []
        api_path = '/season/%s' % playlist_id

        while api_path:
            api_key = _get_api_key(api_path)
            req = self._get_api_request(api_path, api_key)
            data = self._download_json(req, api_path.split('/')[-1])
            items = data['_embedded']['stream:episode']
            if type(items) == list:
                for elem in items:
                    episode_ids.append(str_or_none(elem['id']))
            else:
                episode_ids.append(str_or_none(items['id']))
            next_link = data['_links'].get('next')
            if next_link:
                next_link = str_or_none(next_link.get('href'))
            api_path = next_link
        return episode_ids

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_path = '/show/%s' % display_id.split('/')[0]
        api_key = _get_api_key(api_path)

        req = self._get_api_request(api_path, api_key)
        data = self._download_json(req, display_id)
        title = data.get('name')
        description = data.get('description')

        url_name = str_or_none(data['url_name'])
        extract_all = True if url_name == display_id.split('/')[-1] else False
        playlist_ids = []
        items = data['_embedded']['stream:season']
        if type(items) == list:
            for elem in items:
                url_name = str_or_none(elem['url_name'])
                if extract_all or url.endswith(url_name):
                    playlist_ids.append(str_or_none(elem['id']))
        else:
            playlist_ids.append(str_or_none(items['id']))

        episode_ids = []
        for pid in playlist_ids:
            episode_ids.extend(self._extract_ids_from_playlist(pid))

        return self.playlist_result(
            [self.url_result(
                'streamcz:%s' % eid, ie=StreamCZIE.ie_key()) for eid in episode_ids],
            playlist_id=display_id,
            playlist_title=title,
            playlist_description=description
        )

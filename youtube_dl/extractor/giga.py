# coding: utf-8
from __future__ import unicode_literals

import itertools

from .common import InfoExtractor
from ..utils import (
    qualities,
    compat_str,
    parse_iso8601,
    int_or_none,
    float_or_none,
)


class GigaIE(InfoExtractor):
    _VALID_URL = r'https?://videos\.giga\.de/embed/(?P<id>\d+)'

    def _call_api(self, path, video_id):
        return self._download_json('http://www.giga.de/api/syndication/video/video_id/%s/%s.json' % (video_id, path), video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        default = self._call_api('default', video_id)
        playlist = self._call_api('playlist', video_id)[0]

        quality = qualities(['normal', 'hd720'])

        formats = []
        for format_id in itertools.count(0):
            fmt = playlist.get(compat_str(format_id))
            if not fmt:
                break
            formats.append({
                'url': fmt['src'],
                'format_id': '%s-%s' % (fmt['quality'], fmt['type'].split('/')[-1]),
                'quality': quality(fmt['quality']),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': default['video_title'],
            'thumbnail': default.get('video_image'),
            'formats': formats,
        }


class GigaPostIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?giga\.de/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.giga.de/filme/anime-awesome/trailer/anime-awesome-chihiros-reise-ins-zauberland-das-beste-kommt-zum-schluss/',
        'md5': '6bc5535e945e724640664632055a584f',
        'info_dict': {
            'id': '2622086',
            'display_id': 'anime-awesome-chihiros-reise-ins-zauberland-das-beste-kommt-zum-schluss',
            'ext': 'mp4',
            'title': 'Anime Awesome Chihiros Reise ins Zauberland',
            'description': 'md5:07e8592ab2fe66fd9e051106d888aee8',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 578,
            'timestamp': 1414753306,
            'upload_date': '20141031',
            'uploader': 'Robin Schweiger',
            'view_count': int,
        },
    }, {
        'url': 'http://www.giga.de/games/channel/giga-top-montag/giga-topmontag-die-besten-serien-2014/',
        'info_dict': {
            'id': '2652823',
            'description': 'md5:f83f343e4685b48cc1c872b8d2c45b08',
            'uploader': 'Severin Pick',
            'title': 'GIGA TOPmontag: Die besten Serien 2014',
            'timestamp': 1419854425,
        },
        'playlist': [{
            'md5': '4ab7f2c6054a3257975a8e7ad6b73ada',
            'info_dict': {
                'id': '2652842',
                'ext': 'mp4',
                'title': 'TOPmontag: Die besten Serien 2014 - Teil 1',
                'upload_date': '20141229',
                'uploader': 'Severin Pick',
                'timestamp': 1419854425,
                'duration': 799.0,
                'view_count': int,
            },
        }, {
            'md5': '4227d56ec615013a7f72fae900399ea8',
            'info_dict': {
                'id': '2653854',
                'ext': 'mp4',
                'upload_date': '20141229',
                'title': 'TOPmontag: Die besten Serien 2014 - Teil 2',
                'uploader': 'Severin Pick',
                'timestamp': 1419854425,
                'duration': 829.0,
                'view_count': int,
            },
        }, {
            'md5': '015963162a5d7f31bb5c43e548518981',
            'info_dict': {
                'id': '2652834',
                'ext': 'mp4',
                'upload_date': '20141229',
                'title': 'TOPmontag: Die besten Serien 2014 - BONUS',
                'timestamp': 1419854425,
                'uploader': 'Severin Pick',
                'duration': 283.0,
                'view_count': int,
            },
        }]
    }, {
        'url': 'http://www.giga.de/extra/netzkultur/videos/giga-games-tom-mats-robin-werden-eigene-wege-gehen-eine-ankuendigung/',
        'only_matching': True,
    }, {
        'url': 'http://www.giga.de/tv/jonas-liest-spieletitel-eingedeutscht-episode-2/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        post_data = self._download_json(url + '?content=syndication/key/3c2244f8347e6f3edc482b3acb3674af/meta/json/', display_id)['v1.2']

        post_info = {
            'id': compat_str(post_data['post_id']),
            'display_id': 'anime-awesome-chihiros-reise-ins-zauberland-das-beste-kommt-zum-schluss',
            'title': post_data['title'],
            'description': post_data.get('excerpt'),
            'uploader': post_data.get('author'),
            'timestamp': parse_iso8601(post_data.get('date'), ' '),
        }

        if post_data['type'] == 'video':
            entries = []
            for video in post_data['videos_list']:
                entries.append({
                    '_type': 'url_transparent',
                    'id': compat_str(video['id']),
                    'title': video['title'],
                    'url': 'http://videos.giga.de/embed/%s' % video['id'],
                    'duration': float_or_none(video.get('length')),
                    'view_count': int_or_none(video.get('view_counter')),
                    'uploader': post_info['uploader'],
                    'timestamp': post_info['timestamp'],
                    'ie_key': 'Giga',
                })

            if len(entries) == 1:
                post_info.update(entries[0])
            else:
                post_info.update({
                    '_type': 'multi_video',
                    'entries': entries,
                })
            return post_info

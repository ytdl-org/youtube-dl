# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none, ExtractorError


class SpreakerIE(InfoExtractor):
    IE_NAME = 'spreaker'
    _VALID_URL = r"""(?x)^
        https?://
        (?:www.|api.)?
        spreaker.com/
        (?:
            show/[a-z0-9_-]+|
            user/[a-z0-9_-]+/[a-z0-9_-]|
            episode/(?P<id>[0-9]+)
        )
    """
    _TESTS = [
        {
            'url': 'https://www.spreaker.com/show/success-with-music',
            'info_dict': {
                'title': 'Success With Music',
                'id': 2317431,
            },
            'playlist_mincount': 14,
        },
        {
            'url': ('https://www.spreaker.com/user/9780658/swm-ep15-how-to-'
                    'market-your-music-part-2'),
            'info_dict': {
                'id': '12534508',
                'ext': 'mp3',
                'title': 'Marketing Your Music - Part 2',
                'upload_date': '20170809',
                'uploader': 'SWM',
                'uploader_id': 9780658,
            },
        },
        {
            'url': 'https://api.spreaker.com/episode/12534508',
            'info_dict': {
                'id': '12534508',
                'ext': 'mp3',
                'title': 'Marketing Your Music - Part 2',
                'upload_date': '20170809',
                'uploader': 'SWM',
                'uploader_id': 9780658,
            },
        }
    ]

    def _spreaker_episode_data_to_info(self, data):
        upload_date = data['published_at'][0:10].replace('-', '')
        author = data.get('author')
        if not author:
            author = {}
        stats = data.get('stats')
        view_count = like_count = comment_count = 0
        show = data.get('show')
        if not show:
            show = {}
        else:
            show_image = show.get('image')
        if not show_image:
            show_image = {}

        if stats:
            view_count = (stats.get('plays', 0) +
                          stats.get('plays_streaming', 0) +
                          stats.get('plays_download', 0))
            like_count = stats.get('likes', 0)
            comment_count = stats.get('messages', 0)

        return {
            'id': compat_str(data['episode_id']),
            'title': data['title'],
            'url': data['download_url'],
            'display_id': data.get('permalink'),
            'webpage_url': data.get('site_url'),
            'uploader': author.get('fullname'),
            'creator': author.get('fullname'),
            'release_date': upload_date,
            'upload_date': upload_date,
            'uploader_id': author.get('user_id'),
            'duration': int_or_none(data.get('length')),
            'view_count': int_or_none(view_count),
            'like_count': int_or_none(like_count),
            'comment_count': int_or_none(comment_count),
            'format': 'MPEG Layer 3',
            'format_id': 'mp3',
            'container': 'mp3',
            'ext': 'mp3',
            'thumbnail': show_image.get('big_url'),
            'language': show.get('language'),
            'thumbnails': [
                {
                    'id': show_image.get('image_id'),
                    'url': show_image.get('big_url'),
                    'width': int_or_none(show_image.get('width')),
                    'height': int_or_none(show_image.get('height')),
                },
                {
                    'url': show_image.get('large_url'),
                },
                {
                    'url': show_image.get('medium_url')
                },
                {
                    'url': show_image.get('small_url')
                },
            ],
        }

    def _real_extract(self, url):
        episode_id = self._match_id(url)

        if re.match(r'^[0-9]+$', episode_id):
            data_url = url
        elif '/show/' in url:
            html = self._download_webpage(url, None)
            playlist_url = self._html_search_regex(
                r'data-playlist_url="(?P<url>https\://[^"]+")', html, 'url')
            items = self._download_json(playlist_url, None)
            items = items['response']['playlist']['items']

            if not items:
                raise ExtractorError('Empty playlist')

            urls = [x['api_url'] for x in items]
            ret = []
            for index, url in enumerate(urls):
                data = self._download_json(url, None)['response']['episode']
                dict_ = self._spreaker_episode_data_to_info(data)
                dict_.update({
                    'playlist_id': compat_str(data['show_id']),
                    'playlist_title': data['show']['title'],
                    'playlist_index': index,
                })
                ret.append(dict_)

            return self.playlist_result(ret,
                                        data['show_id'],
                                        data['show']['title'])
        else:
            html = self._download_webpage(url, None)
            episode_id = self._html_search_regex(
                r'data-episode_id="(?P<id>[0-9]+)"', html, 'id')
            if not re.match(r'^[0-9]+$', episode_id):
                raise ExtractorError('Could not find episode ID')
            data_url = 'https://api.spreaker.com/episode/%s' % (episode_id)

        data = self._download_json(data_url, episode_id)['response']['episode']
        if not data['download_enabled']:
            raise ExtractorError('Not supported yet')

        return self._spreaker_episode_data_to_info(data)

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none, ExtractorError


def _spreaker_episode_data_to_info(data):
    published_at = data.get('published_at')
    upload_date = None
    if published_at:
        upload_date = published_at[0:10].replace('-', '')
    author = data.get('author', {})
    stats = data.get('stats', {})
    view_count = like_count = comment_count = None
    show = data.get('show', {})
    show_image = show.get('image', {})

    if stats:
        plays = stats.get('plays')
        plays_streaming = stats.get('plays_streaming')
        plays_download = stats.get('plays_download')
        view_count = None
        for x in [plays, plays_streaming, plays_download]:
            if x is None:
                continue
            if view_count is None:
                view_count = x
            else:
                view_count += x
        like_count = stats.get('likes')
        comment_count = stats.get('messages')

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
        'extractor': 'spreaker',
    }


class SpreakerPlaylistIE(InfoExtractor):
    IE_NAME = 'spreaker:playlist'
    _VALID_URL = r'https?://(?:www\.)?spreaker\.com/show/[a-z0-9_-]+'
    _TEST = {
        'url': 'https://www.spreaker.com/show/success-with-music',
        'info_dict': {
            'title': 'Success With Music',
            'id': 2317431,
        },
        'playlist_mincount': 14,
    }

    def _real_extract(self, url):
        html = self._download_webpage(url, None)
        playlist_url = self._html_search_regex(
            r'data-playlist_url="(?P<url>https\://[^"]+")', html, 'url')
        items = self._download_json(playlist_url,
                                    None,
                                    'Downloading playlist JSON')
        playlist = items['response']['playlist']
        next_url = playlist.get('next_url')
        items = playlist.get('items', [])

        if not items:
            raise ExtractorError('Empty playlist')

        page_no = 2
        download_str = 'Downloading playlist JSON page #%d'
        while next_url:
            items_ = self._download_json(next_url,
                                         None,
                                         download_str % (page_no,))
            playlist_ = items_['response']['playlist']
            new_items = playlist_.get('items', [])
            if not new_items:
                break
            items += new_items
            next_url = playlist_.get('next_url')
            page_no += 1

        urls = [x['api_url'] for x in items]
        entries = []
        for index, url in enumerate(urls):
            data = self._download_json(url, None)['response']['episode']
            dict_ = _spreaker_episode_data_to_info(data)
            entries.append(dict_)

        return self.playlist_result(entries,
                                    data['show_id'],
                                    data['show']['title'])


class SpreakerIE(InfoExtractor):
    IE_NAME = 'spreaker'
    _VALID_URL = (r'https?://(?:(?:api|www)\.)?spreaker\.com/'
                  r'(?:(?:(?:download/)?episode/(?P<id>[0-9]+)'
                  r'(?:/[^\.]+\.mp3$)?)|user/[a-z0-9_-]+/[a-z0-9_-]+)')
    _TESTS = [
        {
            'url': 'https://api.spreaker.com/episode/12534508',
            'info_dict': {
                'id': '12534508',
                'ext': 'mp3',
                'title': 'EP:15 | Music Marketing (Likes) - Part 2',
                'upload_date': '20170809',
                'uploader': 'SWM',
                'uploader_id': 9780658,
            },
        },
        {
            'url': ('https://api.spreaker.com/download/episode/12534508/'
                    'swm_ep15_how_to_market_your_music_part_2.mp3'),
            'info_dict': {
                'id': '12534508',
                'ext': 'mp3',
                'title': 'EP:15 | Music Marketing (Likes) - Part 2',
                'upload_date': '20170809',
                'uploader': 'SWM',
                'uploader_id': 9780658,
            },
        },
        {
            'url': ('https://www.spreaker.com/user/9780658/swm-ep15-how-to-'
                    'market-your-music-part-2'),
            'info_dict': {
                'id': '12534508',
                'ext': 'mp3',
                'title': 'EP:15 | Music Marketing (Likes) - Part 2',
                'upload_date': '20170809',
                'uploader': 'SWM',
                'uploader_id': 9780658,
            },
        }
    ]

    def _real_extract(self, url):
        episode_id = self._match_id(url)
        if re.match(r'^[0-9]+$', episode_id):
            url = 'https://api.spreaker.com/episode/%s' % (episode_id,)
        else:
            html = self._download_webpage(url,
                                          None,
                                          note='Downloading episode page')
            episode_id = self._html_search_regex(
                r'data-episode_id="(?P<id>[0-9]+)"', html, 'id')
            if not re.match(r'^[0-9]+$', episode_id):
                raise ExtractorError('Could not find episode ID')
            url = 'https://api.spreaker.com/episode/%s' % (episode_id)

        data = self._download_json(url, episode_id)['response']['episode']
        if not data['download_enabled']:
            raise ExtractorError('Not supported yet')

        return _spreaker_episode_data_to_info(data)

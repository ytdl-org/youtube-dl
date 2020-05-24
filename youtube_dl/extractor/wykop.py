# coding=utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    url_or_none,
)


class WykopIE(InfoExtractor):
    _VALID_URL = r'(?P<url>https?://(?:[^/]+\.)?wykop\.pl/(?P<type>link|wpis)/(?P<main_id>\d+)/(?:comment/\d+/|(?P<display_id>[^/#]+)/?){0,2}(?:#comment-(?P<comment_id>\d+))?$)'
    _TESTS = [{
        # youtube @ link
        'url': 'https://www.wykop.pl/link/5515619/prof-obirek-o-pedofilii-wsrod-duchownych-jan-pawel-2-wiedzial-i-nic-nie-zrobil/',
        'info_dict': {
            'id': 'CQoJ7TQjrI4',
            'ext': 'webm',
            'title': 'Prof. Obirek o pedofilii wśród duchownych: Jan Paweł 2 wiedział i nic nie zrobił',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'invisibleborder',
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 0,
            'upload_date': '20200519',
            'description': 'md5:3f6e7f7fd2cad0a312e030987517b7b3',
            'uploader_id': 'onetnews',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }, {
        'url': 'https://www.wykop.pl/link/5515619/',
        'only_matching': True,
    }, {
        # youtube @ link comment
        'url': 'https://www.wykop.pl/link/5517513/#comment-77502323',
        'info_dict': {
            'id': 'rIHIxNha_FE',
            'ext': 'mp4',
            'title': '@LrPrl: Już niedługo...',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'RzecznikNASA',
            'like_count': int,
            'dislike_count': int,
            'comment_count': None,
            'age_limit': 0,
            'upload_date': '20150811',
            'description': 'md5:a5eb775ff886debe6abb43e1a43a7fbc',
            'uploader_id': 'UCMT04abyhI8FVVu_uxy-rkA',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }, {
        'url': 'https://www.wykop.pl/link/5504073/comment/77196337/#comment-77196337',
        'only_matching': True,
    }, {
        # streamable @ entry
        'url': 'https://www.wykop.pl/wpis/49614397/',
        'only_matching': True,
    }, {
        # gfycat @ entry
        'url': 'https://www.wykop.pl/wpis/49579089/kiedy-skryptujesz-zaczynajac-tablice-od-1-programo/',
        'info_dict': {
            'id': 'polishedmarriedgoral',
            'ext': 'mp4',
            'title': 'Kiedy skryptujesz zaczynając tablicę od [1]\n#programowanie #heheszki #2jednostkowe0integracyjnych',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Acri',
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'age_limit': 0,
            'upload_date': '20200521',
            'timestamp': 1590097062,
        },
        'params': {
            'format': 'best',
            'skip_download': True,
        },
    }, {
        # youtube @ entry comment
        'url': 'https://www.wykop.pl/wpis/49583499/#comment-175441409',
        'info_dict': {
            'id': 'qa3KvvJhmbk',
            'ext': 'mp4',
            'title': '@KsiundzRobak: nic nowego ¯\\_(ツ)_/¯\nOd dawna jest wiadomo, że taki jest poziom wyborców PiSu:',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Alex_Krycek',
            'like_count': int,
            'dislike_count': int,
            'comment_count': None,
            'age_limit': 0,
            'upload_date': '20121114',
            'description': 'Wolność słowa wg PiS. Awantura w trakcie spotkania Antoniego Macierewicza w Czeladzi.\nWięcej na www.Czeladz24.com - zamieszczać na swoich stronach proszę tylko i wyłącznie ze źródłem, podając www.Czeladz24.com',
            'uploader_id': 'kondipr1988',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }, {
        # youtube @ entry comment
        'url': 'https://www.wykop.pl/wpis/49583499/dzien-dobry-serdecznie-chcialbym-dzis-zaprezentowa/#comment-175441409',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url, entity_type, main_id, comment_id, display_id = mobj.group('url', 'type', 'main_id', 'comment_id', 'display_id')

        api_url = 'https://a2.wykop.pl/%s/%s/%s/appkey/aNd401dAPp' % ('links' if entity_type == 'link' else 'entries', 'comment' if comment_id is not None else 'link' if entity_type == 'link' else 'entry', comment_id or main_id)

        data = self._download_json(
            api_url, entity_type[0] + (('c' + comment_id) if comment_id is not None else main_id))['data']

        if comment_id is not None or entity_type == 'wpis':
            video_url = data['embed']['url']
            if data['embed']['type'] == 'animated':
                video_url = video_url.replace('.jpg', '.gif')
        elif entity_type == 'link':
            video_url = data['source_url']

        embed_or_data = data['embed'] if 'embed' in data else data

        over_18 = embed_or_data['plus18']
        if over_18 is True:
            age_limit = 18
        elif over_18 is False:
            age_limit = 0
        else:
            age_limit = None

        return {
            '_type': 'url_transparent',
            'url': video_url,
            'title': data['title'] if 'title' in data else clean_html(data['body']) if 'body' in data else '',
            'alt_title': data['description'] if 'description' in data else None,
            'display_id': display_id,
            'thumbnail': url_or_none(embed_or_data['preview']),
            'uploader': data['author']['login'],
            'like_count': int_or_none(data['vote_count_plus'] if 'vote_count_plus' in data else data['vote_count']),
            'dislike_count': int_or_none(data['bury_count'] if 'bury_count' in data else (data['vote_count'] - data['vote_count_plus']) if 'vote_count_plus' in data else None),
            'comment_count': int_or_none(data['comments_count'] if 'comments_count' in data else None),
            'age_limit': age_limit,
        }

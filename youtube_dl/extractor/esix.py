# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class esixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:e621|e926).net/posts/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://e621.net/posts/2429748',
        'md5': 'f2b2773d3de744141ed999af74b73391',
        'info_dict': {
            'id': '2429748',
            'ext': 'webm',
            'title': '0bfc03a8b40f6e4bff3df2c376b14f37',
            'thumbnail': 'https://static1.e621.net/data/sample/0b/fc/0bfc03a8b40f6e4bff3df2c376b14f37.jpg',
            'description': 'From source:\r\n[quote]\r\nPorter Robinson - Something Comforting \r\nhttps://youtu.be/-C-2AqRD8io\r\n\r\nCollaboration with Porter Robinson.\r\nポーター・ロビンソンとのオフィシャルコラボです。\r\n\r\n------------------------------------\r\n\r\n■ブルーハムハムとは？\r\n音を食べて生きている\"宇宙ハムスター\"。不運なことに地球旅行の途中で迷子になり、地球人に拾われる。人間社会のさまざまな音を食べて、その美味しさに驚愕。地球上のいろんな音楽を味わうことが夢になった。\r\n\r\nTwitter：https://twitter.com/THEBLUEHAMHAM\r\nInstagram：https://www.instagram.com/thebluehamham/\r\n[/quote]'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._download_json(url + '.json', video_id).get('post')
        fmts = ['webm', 'mp4']
        ext = post.get('file').get('ext')

        if ext not in fmts:
            raise ExtractorError('Specified post is not a video', expected=True)

        return {
            'id': video_id,
            'title': post.get('file').get('md5'),
            'url': post.get('file').get('url'),
            'ext': ext,
            'thumbnail': post.get('sample').get('url'),
            'description': post.get('description')
        }

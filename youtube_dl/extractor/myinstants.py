# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import determine_ext, int_or_none


class MyinstantsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?myinstants\.com/instant/(?P<id>[a-z0-9\-]+)'
    _TESTS = [{
        'url': 'https://www.myinstants.com/instant/nani-sore/',
        'md5': '04a16d1b4ed106047c4c1b9d2f9b7e73',
        'info_dict': {
            'id': 'nani-sore',
            'ext': 'mp3',
            'title': 'NANI SORE',
            'thumbnail': 'https://www.myinstants.com/media/instants_images/maxresdefault_11.jpg',
            'uploader': 'kucheroako',
            'uploader_id': 'kucheroako',
            'uploader_url': 'https://www.myinstants.com/profile/kucheroako',
            'categories': ['Anime & Manga']
        }
    }, {
        'url': 'https://www.myinstants.com/instant/windows-xp-error/',
        'md5': 'b63e5aaa1c2fbc010688c2f5abe405a5',
        'info_dict': {
            'id': 'windows-xp-error',
            'ext': 'mp3',
            'title': 'Windows XP Error',
            'uploader': 'omarjunior',
            'uploader_id': 'omarjunior',
            'uploader_url': 'https://www.myinstants.com/profile/omarjunior',
            'categories': ['Memes']
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h1[^>]+id=(["\'])instant-page-title\1[^>]*>(?P<title>[^<]+)',
            webpage, 'title', group='title')
        uploader = self._search_regex(r'<div>Uploaded by <a href="/profile/([^/]+)/">', webpage, 'uploader', fatal=False)
        file_url = self._og_search_property('audio', webpage)

        return {
            'id': video_id,
            'ext': determine_ext(file_url),
            'title': title,
            'url': file_url,
            'thumbnail': self._og_search_property('image', webpage, fatal=False),
            'uploader': uploader,
            'uploader_id': uploader,
            'uploader_url': 'https://www.myinstants.com/profile/' + uploader,
            'view_count': int_or_none(self._search_regex(
                r'<div>Uploaded by <a href="/profile/(?P<user>[^/]+)/">(?P<user2>[^/]+)</a> - (?P<views>[0-9,]+) views',
                webpage, 'views', fatal=False)),
            'like_count': int_or_none(self._search_regex(
                r'<b>([0-9,]+) users</b>\sfavorited this sound button',
                webpage, 'likes', fatal=False)),
            'categories': [self._html_search_regex(
                r'<a href="/categories/(?P<caturl>[^/]+)/" title="(?P<cat>.+)">',
                webpage, 'cat', group='cat', fatal=False)]
        }

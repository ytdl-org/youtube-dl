# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none, mimetype2ext, str_or_none, try_get, url_or_none


class CriterionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?criterion\.com/films/(?P<id>\d+)-.+'
    _TESTS = [
        {
            'url': 'http://www.criterion.com/films/184-le-samourai',
            'md5': 'e80a6ec09375c58e0050b809238c4d39',
            'info_dict': {
                'id': '265399901',
                'title': 'Le samouraï',
                'ext': 'mp4',
                'description': 'md5:56ad66935158c6c88d4e391397c00d22',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.criterion.com/films/28986-the-heiress',
            'md5': '7178b368986eed7c9bf362dd90472c74',
            'info_dict': {
                'id': '315291282',
                'title': 'The Heiress',
                'ext': 'mp4',
                'description': 'md5:3d34fe5e6ff5520998b13137eba0f7ce',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.criterion.com/films/28836-funny-games',
            'md5': '6e36a90749755e600eeb57dc632e920d',
            'info_dict': {
                'id': '316586307',
                'title': 'Funny Games',
                'ext': 'mp4',
                'description': 'md5:64326c0cd08a6a582c10d63349941250',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.criterion.com/films/613-the-magic-flute',
            'md5': '8458ac11d5809f3f2d8f9aec1afa2fd6',
            'info_dict': {
                'id': '305845790',
                'title': 'The Magic Flute',
                'ext': 'mp4',
                'description': 'md5:9f232dcf15d9861c6a551662973482a5',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
    ]

    def _extract_embedded_url(self, pattern, html, group):
        return self._search_regex(pattern, html, 'embedded url', group=group)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=None) or self._html_search_meta(
            'twitter:title', webpage
        )
        description = self._og_search_description(
            webpage, default=None
        ) or self._html_search_meta('twitter:description', webpage, fatal=False)

        # Follow embedded url
        embedded_re = r'<iframe[^>]+?src=["\'](?P<url>https?:\/\/player\.vimeo\.com\/video\/(?P<id>\d+)\?[^"\']+?)["\']'
        embedded_id = str_or_none(
            self._extract_embedded_url(embedded_re, webpage, group='id')
        )
        embedded_url = url_or_none(
            self._extract_embedded_url(embedded_re, webpage, group='url')
        )

        embedded_webpage = self._download_webpage(
            embedded_url, embedded_id, headers={'Referer': url}
        )

        # Parse json data
        data_re = r'var\s*config\s*=\s*(?P<data>.*?);'
        data_str = self._search_regex(
            data_re, embedded_webpage, 'json data', group='data'
        )
        data = self._parse_json(data_str, embedded_id)

        final_id = str_or_none(try_get(data, lambda x: x['video']['id']))

        videos = try_get(data, lambda x: x['request']['files']['progressive'], list)
        formats = []
        for vid in videos:
            formats.append(
                {
                    'url': url_or_none(vid.get('url')),
                    'ext': mimetype2ext(vid.get('mime')),
                    'resolution': str_or_none(vid.get('quality')),
                    'height': int_or_none(vid.get('height')),
                    'width': int_or_none(vid.get('width')),
                    'fps': int_or_none(vid.get('fps')),
                }
            )
        formats.sort(key=lambda x: x['height'])

        thumb_data = try_get(data, lambda x: x['video']['thumbs'], dict)
        thumbnails = []
        for url in thumb_data:
            thumbnails.append({'url': url_or_none(thumb_data[url])})

        return {
            'id': final_id,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnails': thumbnails,
        }

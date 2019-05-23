# coding: utf-8
from __future__ import unicode_literals

import re

from ..utils import RegexNotFoundError, str_or_none, url_or_none
from .vimeo import VimeoBaseInfoExtractor


class CriterionIE(VimeoBaseInfoExtractor):
    IE_NAME = 'criterion'
    IE_DESC = 'The Criterion Collection'
    _VALID_URL = r'https?://(?:www\.)?criterion\.com/films/(?P<id>\d+)-.+'
    _TESTS = [
        {
            'url': 'http://www.criterion.com/films/184-le-samourai',
            'info_dict': {
                'id': '265399901',
                'title': 'Le samouraï',
                'description': 'md5:56ad66935158c6c88d4e391397c00d22',
                'uploader': 'Criterion Collection',
                'uploader_id': 'criterioncollection',
                'uploader_url': 'https://vimeo.com/criterioncollection',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/28986-the-heiress',
            'info_dict': {
                'id': '315291282',
                'title': 'The Heiress',
                'description': 'md5:3d34fe5e6ff5520998b13137eba0f7ce',
                'uploader': 'Criterion Collection',
                'uploader_id': 'criterioncollection',
                'uploader_url': 'https://vimeo.com/criterioncollection',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/28836-funny-games',
            'info_dict': {
                'id': '316586307',
                'title': 'Funny Games',
                'description': 'md5:64326c0cd08a6a582c10d63349941250',
                'uploader': 'Criterion Collection',
                'uploader_id': 'criterioncollection',
                'uploader_url': 'https://vimeo.com/criterioncollection',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.criterion.com/films/613-the-magic-flute',
            'info_dict': {
                'id': '305845790',
                'title': 'The Magic Flute',
                'description': 'md5:9f232dcf15d9861c6a551662973482a5',
                'uploader': 'Criterion Collection',
                'uploader_id': 'criterioncollection',
                'uploader_url': 'https://vimeo.com/criterioncollection',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
            'params': {'skip_download': True},
        },
    ]

    @staticmethod
    def _extract_video_id_and_url(webpage):
        emb_re = r'<iframe[^>]+?src=["\'](?P<url>https?:\/\/player\.vimeo\.com\/video\/(?P<id>\d+)\?[^"\']+?)["\']'

        mobj = re.search(emb_re, webpage)
        if mobj is None:
            raise RegexNotFoundError('Unable to extract embedded id and url.')

        emb_id = str_or_none(mobj.group('id'))
        emb_url = url_or_none(mobj.group('url'))

        return (emb_id, emb_url)

    def _get_config(self, webpage, video_id):
        config_re = r'var\s*config\s*=\s*(?P<data>.*?);'
        config_str = self._search_regex(
            config_re, webpage, 'json config data', group='data'
        )

        return self._parse_json(config_str, video_id)

    def _real_extract(self, url):
        criterion_id = self._match_id(url)
        criterion_webpage = self._download_webpage(url, criterion_id)

        title = self._og_search_title(
            criterion_webpage, default=None
        ) or self._html_search_meta('twitter:title', criterion_webpage)
        description = self._og_search_description(
            criterion_webpage, default=None
        ) or self._html_search_meta(
            'twitter:description', criterion_webpage, fatal=False
        )

        video_id, video_url = CriterionIE._extract_video_id_and_url(criterion_webpage)

        video_webpage = self._download_webpage(
            video_url, video_id, headers={'Referer': url}
        )

        config = self._get_config(video_webpage, video_id)

        info_dict = self._parse_config(config, video_id)
        self._vimeo_sort_formats(info_dict['formats'])

        info_dict['id'] = video_id
        info_dict['title'] = title
        info_dict['description'] = description

        return info_dict

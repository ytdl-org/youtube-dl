# coding: utf-8
from __future__ import unicode_literals

import re
import sys

from ..jsinterp import JSInterpreter
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext, int_or_none,
    unified_strdate,
    js_to_json)


class YouWatchIE(InfoExtractor):
    _VALID_URL = r'^(https?://(?:www\.)?youwatch\.org/)(?P<embed>embed-)?(?P<id>[a-z0-9]+)(\.html)?$'
    _TESTS = [
        {
            'url': 'http://youwatch.org/ncvag7qib06a',
            'md5': 'fcc3d1b77d41921ab408ddfbc51604b1',
            'info_dict': {
                'id': 'ncvag7qib06a',
                'ext': 'mp4',
                'title': 'A 4 mesterl v sz',
                'thumbnail': 'http://212.7.205.2/i/03/00000/ncvag7qib06a.jpg',
                'upload_date': '20140710',
                'view_count': int
            }
        }, {
            'url': 'http://youwatch.org/r4gmiun6qx57',
            'md5': '71a151e542ae86a023d8cc57e243a917',
            'info_dict': {
                'id': 'r4gmiun6qx57',
                'ext': 'mp4',
                'title': 'A h�z 2 A m�sodik t�rt�net',
                'thumbnail': 'http://212.7.211.67/i/05/00000/r4gmiun6qx57.jpg',
                'upload_date': '20150509',
                'view_count': int
            }
        }, {
            'url': 'http://youwatch.org/t179wlmqbndd',
            'md5': '1984ebed1fb5fee33aa7076a73faffa3',
            'info_dict': {
                'id': 't179wlmqbndd',
                'ext': 'mp4',
                'title': 'bd-ijf',
                'thumbnail': 'http://212.7.211.67/i/04/00000/t179wlmqbndd.jpg',
                'upload_date': '20150523',
                'view_count': int
            }
        }, {
            'url': 'http://youwatch.org/embed-2a3y6svmsofw.html',
            'md5': 'ded91fbca8c913d493263ae26e5e18d1',
            'info_dict': {
                'id': '2a3y6svmsofw',
                'ext': 'mp4',
                'title': 'A Vadnyugat v�gnapjai (2008)',
                'thumbnail': 'http://212.7.211.68/i/05/00362/0iy24azid2xj.jpg',
                'upload_date': '20140223',
                'view_count': int
            }
        }
    ]

    @staticmethod
    def __v_rot(text):
        if text is None:
            return None
        rotated = ''
        for letter in text:
            l_code = ord(letter)
            if 64 < l_code < 91:  # ord('A'): 65 ord('Z'): 90
                rotated += chr((l_code - 65 - 13) % 26 + 65)
            elif 96 < l_code < 123:  # ord('a'): 97 ord('z'): 122
                rotated += chr((l_code - 97 - 13) % 26 + 97)
            else:
                rotated += letter
        return rotated

    def _real_extract(self, url):
        video_id = self._match_id(url)
        embed_url = None
        if self._VALID_URL_RE.match(url).group('embed') is not None:
            embed_url = url
            url = self._VALID_URL_RE.sub(r'\1\g<id>', url)
        webpage = self._download_webpage(url, video_id)

        if 'This server is in maintenance mode. Refresh this page in some minutes.' in webpage:
            raise ExtractorError('Video is temporally unavailable. ',
                                 sys.exc_info()[2], True, video_id=video_id)
        if 'The file you were looking for could not be found, sorry for any inconvenience.' in webpage:
            raise ExtractorError('Video is gone. ',
                                 sys.exc_info()[2], True, video_id=video_id)

        title = self._html_search_regex(r'''<h3\s+.*id=("|')title\1.*>\s*(?P<title>.+?)\s*<\s*/''',
                                        webpage, 'title', fatal=False,
                                        flags=re.IGNORECASE, group='title')
        title = self.__v_rot(title)

        ul_date = self._html_search_regex(r'''<i\s.*class=("|')fa fa-calendar\1.*>\s*</i>\s*on\s+(?P<date>.*)\s*<''',
                                          webpage, 'upload date', fatal=False,
                                          flags=re.MULTILINE | re.IGNORECASE, group='date')
        ul_date = unified_strdate(ul_date, day_first=False)

        views = self._html_search_regex(r'''<\s*([^\s]+).*title=("|')views\2.*>\s*(?P<count>.*)\s*<\s*\/\s*\1\s*>''',
                                        webpage, 'views', fatal=False,
                                        flags=re.IGNORECASE, group='count')
        views = int_or_none(views)

        if embed_url is None:
            embed_url = self._html_search_regex(
                r'''<iframe[^>]+class=("|')embed-responsive-item\1[^>]+src=("|')(?P<url>((?!\2).)+)\2''',
                webpage, 'embed url', flags=re.IGNORECASE, group='url')

        embed_html = self._download_webpage(embed_url, video_id)
        ref_url = self._html_search_regex(
            r'''<iframe[^>]+src=("|')(?P<url>((?!\1).)+)\1''',
            embed_html, 'referer', flags=re.IGNORECASE, group='url')

        embed_html = self._download_webpage(ref_url, video_id)

        jwplayer_setup_script = self._html_search_regex(
            r'''<span\b.*id=("|')vplayer\1[^>]*>\s*<img\b[^>]*>\s*</span>\s*''' +
            r'''<script\b[^>]*type=("|')((?!\2).)*\2[^>]*>(?P<script>((?!</script>).|\s)*)''',
            embed_html, 'jwplayer setup script', flags=re.IGNORECASE, group='script'
        )

        jwplayer_setup = self._html_search_regex(r'(jwplayer\s*\((.|\n)*\)\.setup)',
                                           jwplayer_setup_script, 'jwplayer')

        js = JSInterpreter(jwplayer_setup_script)
        jwplayer_json = js.extract_arguments(jwplayer_setup)
        jwplayer_json = js_to_json(jwplayer_json)
        jwplayer_json = self._parse_json(jwplayer_json, video_id)

        video_urls = [
            {
                'url': source['file'],
                'format_id': source['label'],
                'ext': determine_ext(source['file'])
            } for source in jwplayer_json['sources']
        ]

        info_dict = {'id': video_id, 'formats': video_urls, 'http_headers': {'Referer': ref_url}}
        if jwplayer_json['image'] is not None:
            info_dict['thumbnail'] = jwplayer_json['image']
        if title is not None:
            info_dict['title'] = title
        if ul_date is not None:
            info_dict['upload_date'] = ul_date
        if views is not None:
            info_dict['view_count'] = views

        return info_dict

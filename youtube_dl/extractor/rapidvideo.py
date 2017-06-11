# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    sanitized_Request,
    determine_ext,
    ExtractorError,
    int_or_none
)

import re


class RapidVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rapidvideo\.(cool|org)/(?P<id>[a-zA-Z0-9-_]+)'
    _TEST = {
        'url': 'http://www.rapidvideo.cool/b667kprndr8w/skyrim_no-audio_1080.mp4.html',
        'md5': '99fd03701e3ee9f826ac2fcc11d21c02',
        'info_dict': {
            'id': 'b667kprndr8w',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
        }
    }

    # Function ref: http://code.activestate.com/recipes/65212/
    @staticmethod
    def _baseN(num, b, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
        return ((num == 0) and "0") or (RapidVideoIE._baseN(num // b, b).lstrip("0") + numerals[num % b])

    def _decrypt(self, text):
        match = re.search(r"eval.*?}\('(?P<p>.*?)(?<!\\)',(?P<a>\d+),(?P<c>\d+),'(?P<k>.*?)(?<!\\)'", text)
        if match is None:
            raise ExtractorError('Error while decrypting', expected=True)
        p = match.group('p')
        k = match.group('k').split('|')
        a = int_or_none(match.group('a'))
        c = int_or_none(match.group('c'))
        if a is None or c is None:
            raise ExtractorError('Error while decrypting', expected=True)
        while(True):
            c -= 1
            if k[c] is not None and k[c] != '':
                p = re.subn(r'\b{}\b'.format(RapidVideoIE._baseN(c, a)), k[c], p)[0]
            if (c == 0):
                break
        return p

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        hash_ = self._search_regex(r'<input[^>]+name=["\']hash[^>]+value=["\'](?P<hash>[^<]+)["\']',
                                   webpage, 'hash', group='hash')

        req = sanitized_Request('http://www.rapidvideo.cool/%s' % video_id,
                                data=urlencode_postdata({'op': 'download1',
                                                         'usr_login': '',
                                                         'id': video_id,
                                                         'fname': '',
                                                         'referer': '',
                                                         'hash': hash_,
                                                         'imhuman': 'Watch'
                                                         })
                                )

        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0')
        req.add_header('Referer', 'http://www.rapidvideo.cool/%s' % video_id)

        webpage = self._download_webpage(req, video_id)
        match = re.search(r'tv_file_name=[\'|"](?P<title>[^\'|"]+).*?file:[\'|"](?P<video>[^\'|"]+)',
                          self._decrypt(webpage))

        if match is None:
            raise ExtractorError('Error while extracting video %s' % video_id, expected=True)

        title = match.group('title')
        video_url = match.group('video')
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': determine_ext(video_url, 'mp4')
        }

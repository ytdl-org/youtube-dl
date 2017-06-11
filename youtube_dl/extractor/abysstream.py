# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    ExtractorError,
    urlencode_postdata,
)

import re


class AbySStreamIE(InfoExtractor):
    _SITES = [
        (r'abysstream\.com', 'AbySStream'),
        (r'akstream\.video', 'aKstream')
    ]
    _VALID_URL = (r'https?://(?P<host>(?:www\.)?(?:%s))/(?:v/|video/|stream/)(?P<id>[0-9a-zA-Z]+)'
                  % '|'.join(site for (site, name) in _SITES))
    _TESTS = [{
        'url': 'http://abysstream.com/video/lelzy3mo8rlx',
        'md5': 'efdee8eb17d96bd805e2b6305726ac80',
        'info_dict': {
            'id': 'lelzy3mo8rlx',
            'ext': 'mp4',
            'title': 'Sigle cartoni animati - BATMAN.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://akstream.video/v/85qm9sh87qsn',
        'md5': '270c2425b6b8d536ea8c30ad70b712e3',
        'info_dict': {
            'id': '85qm9sh87qsn',
            'ext': 'mp4',
            'title': 'Sintel - Third Open Movie by Blender Foundation-eRsGyueVLvQ.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        fields = self._hidden_inputs(webpage)

        if fields.get('streamLink') is None:
            raise ExtractorError('File not found', expected=True)

        webpage = self._download_webpage(
            'http://%s/viewvideo.php' % mobj.group('host'),
            video_id, 'Downloading video page',
            data=urlencode_postdata(fields), headers={
                'Referer': url,
                'Content-type': 'application/x-www-form-urlencoded',
            })

        video_url = self._search_regex(
            r'<source[^>]+src=(?:\'|")(?P<video_url>.*?)(?:\'|")',
            webpage, 'video_url', group='video_url')

        poster = video_url.rsplit('.', 1)[0] + '.jpg'

        title = self._html_search_regex(
            (r'<title>(.+?)</title>', r'<b>(.+?)</b>'), webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': poster,
            'ext': determine_ext(video_url, 'mp4')
        }

# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_timestamp,
    unified_strdate,
    parse_duration,
    str_to_int,
)


class PornFlipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornflip\.com(?:/v||/embed)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.pornflip.com/k27gGfg7cqt/green-hair',
        'info_dict': {
            'id': 'k27gGfg7cqt',
            'ext': 'mp4',
            'title': 'Green hair',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 992,
            'timestamp': 1555970182,
            'upload_date': '20190422',
            'uploader_id': '402056',
            'uploader': 'berserk993',
            'view_count': int,
            'age_limit': 18,
            'only_matching': True
        },
        'params': {
            'skip_download': False,
        }
    }, {
        'url': 'https://www.pornflip.com/v/wz7DfNhMmep',
        'md5': '98c46639849145ae1fd77af532a9278c',
        'info_dict': {
            'id': 'wz7DfNhMmep',
            'ext': 'mp4',
            'title': '2 Amateurs swallow make his dream cumshots true',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 112,
            'timestamp': 1481655502,
            'upload_date': '20161213',
            'uploader_id': '106786',
            'uploader': 'figifoto',
            'view_count': int,
            'age_limit': 18,
            'only_matching': True
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://www.pornflip.com/embed/wz7DfNhMmep',
        'only_matching': True,
    }, {
        'url': 'https://www.pornflip.com/v/EkRD6-vS2-s',
        'only_matching': True,
    }, {
        'url': 'https://www.pornflip.com/embed/EkRD6-vS2-s',
        'only_matching': True,
    }, {
        'url': 'https://www.pornflip.com/v/NG9q6Pb_iK8',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.pornflip.com/v/%s' % video_id, video_id)

        mpd_url = self._search_regex(r'data-src=[\'\"](.*?)[\'\"]', webpage, 'mpd_url', fatal=False).replace(r'&amp;', r'&')
        mpd_id = (mpd_url.split('/')[4] or 'DASH')
        formats = list()
        formats.extend(self._extract_mpd_formats(mpd_url, video_id, mpd_id=mpd_id,))
        self._sort_formats(formats)

        title, uploader = self._search_regex('<title>(.*?)</title>', webpage, 'title').rsplit(',', 1)
        title = title.strip()
        uploader = uploader.strip()

        thumbnail = self._search_regex(r'background:\s*?url\((.*?)\)', webpage, 'thumbnail', default=None)

        views = str_to_int(self._search_regex(r'<strong class=\"views\">\s*?<span>(.*?)</span>', webpage, 'views'))
        uploader_id_regex = re.compile(r'item=(\d+?)\&')
        uploader_id = re.findall(uploader_id_regex, webpage)[0]
        upload_date = self._html_search_meta('uploadDate', webpage, 'upload_date')

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'url': mpd_url,
            'thumbnail': thumbnail,
            'duration': int_or_none(parse_duration(self._html_search_meta(
                'duration', webpage, 'duration'))),
            'timestamp': unified_timestamp(upload_date),
            'upload_date': unified_strdate(upload_date),
            'uploader_id': uploader_id,
            'uploader': uploader,
            'view_count': int_or_none(views),
            'age_limit': 18,
        }

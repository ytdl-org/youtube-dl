# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    NO_DEFAULT,
    str_to_int,
)


class XNXXIE(InfoExtractor):
    _VALID_URL = r'https?://(?:video|www)\.xnxx\.com/video-?(?P<id>[0-9a-z]+)/'
    _TESTS = [{
        'url': 'http://www.xnxx.com/video-55awb78/skyrim_test_video',
        'md5': '73c071a361a09aae7e7d60008221fd13',
        'info_dict': {
            'id': '55awb78',
            'ext': 'mp4',
            'title': 'Skyrim Test Video',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 469,
            'view_count': int,
            'age_limit': 18,
            'tags': ['video game', 'skyrim', '3d', 'game', '3d game', 'video games', 'rule34', 'test', 'rough', 'sfm', 'fallout', 'porno game', 'skyrim hentai', 'h game', '3d horse', '3d porno anime', 'xx video wwxxx cartoon cartoons', 'gaming', 'games', '3d porno desenho'],
            'uploader': 'Glurp',
            'uploader_id': 'Glurp',
            'uploader_url': '/porn-maker/glurp',
        },
    }, {
        'url': 'http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_',
        'only_matching': True,
    }, {
        'url': 'http://www.xnxx.com/video-55awb78/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        def get(meta, default=NO_DEFAULT, fatal=True):
            return self._search_regex(
                r'set%s\s*\(\s*(["\'])(?P<value>(?:(?!\1).)+)\1' % meta,
                webpage, meta, default=default, fatal=fatal, group='value')

        title = self._og_search_title(
            webpage, default=None) or get('VideoTitle')

        formats = []
        for mobj in re.finditer(
                r'setVideo(?:Url(?P<id>Low|High)|HLS)\s*\(\s*(?P<q>["\'])(?P<url>(?:https?:)?//.+?)(?P=q)', webpage):
            format_url = mobj.group('url')
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=1, m3u8_id='hls', fatal=False))
            else:
                format_id = mobj.group('id')
                if format_id:
                    format_id = format_id.lower()
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'quality': -1 if format_id == 'low' else 0,
                })
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage, default=None) or get(
            'ThumbUrl', fatal=False) or get('ThumbUrl169', fatal=False)
        duration = int_or_none(self._og_search_property('duration', webpage))
        view_count = str_to_int(self._search_regex(
            r'-.+?\t+- (?P<views>.+?) <span class="icon-f icf-eye">', webpage, 'view count', group='views',
            default=0))

        tags = self._search_regex(r'<meta name="keywords" content="porn,porn movies,free porn,free porn movies,sex,porno,free sex,tube porn,tube,videos,full porn,xxnx,xnxxx,xxx,pussy,(?P<tags>.+?)"', webpage, 'tags', group='tags', default='').split(',')

        uploader_data = re.findall(r'<a class=".+?-plate" href="(?P<uploader_url>.+?)">(?P<uploader_name>.+?)</a>', webpage)
        uploader_id = ''
        uploader_url = ''
        if uploader_data is not None:
            uploader_id = uploader_data[0][1]
            uploader_url = uploader_data[0][0]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats,
            'tags': tags,
            'uploader': uploader_id,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
        }

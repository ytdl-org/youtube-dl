# coding: utf-8
from __future__ import unicode_literals

import re
from ..utils import (
    ExtractorError,
    unescapeHTML,
    js_to_json,
)
from .common import InfoExtractor


class MemriIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?memri(?:tv)?.org/(?:clip(?:/[^/]+)*/(?P<id>\d+)\.html?|.+clip_id=(?P<eid>\d+))'
    IE_NAME = 'memri'
    _TESTS = [{
        'url': 'http://www.memritv.org/clip/en/4496.htm',
        'info_dict': {
            'id': '4496',
            'ext': 'mp4',
            'title': 'Takfiri, The Caliph\'s Favorite Cheese - Anti-ISIS Iraqi Satire',
            'uploader': 'Memri',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('eid')
        rurl = url
        if mobj.groupdict().get('eid') is None:
            rurl = 'http://www.memritv.org/embedded_player/index.php?clip_id=' + video_id

        webpage = self._download_webpage(rurl, video_id)
        jstr = self._search_regex(r'var config_overrides =.+?({.+?});', webpage, 'json', flags=re.DOTALL)
        jstr = re.sub(r'\n\s*//.*?\n', '\n', jstr)  # // comments break js_to_json
        js = self._parse_json(jstr, 'json', transform_source=js_to_json)

        formats = []
        for ent in js['media']['source']:
            eurl = ent.get('src')
            if ent.get('type', '') == 'application/x-mpegURL':
                formats.extend(self._extract_m3u8_formats(
                    eurl, video_id, entry_protocol='m3u8', ext='mp4',
                    m3u8_id='m3u8-mp4',
                    preference=0)
                )
                continue
            proto = re.search(r'^(.+?)://', eurl).group(1)
            format = {
                'url': eurl,
                'ext': 'mp4',
                'protocol': proto,
                'format_id': proto + '-mp4',
            }
            if proto == 'rtmp':
                urlre = re.search(r'^(.+?)(mp4:[^\?]+)(.+)', eurl)
                format['url'] = urlre.group(1) + urlre.group(3)
                format['play_path'] = urlre.group(2)
            formats.append(format)
        if not formats:
            if self._downloader.params.get('verbose', False):
                raise ExtractorError('No video found in ' + jstr + '\n')
            else:
                raise ExtractorError('No video found')

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': unescapeHTML(js['media']['title']),
            'uploader': 'Memri',
            'formats': formats,
        }
